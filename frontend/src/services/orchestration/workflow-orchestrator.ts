import type { Workflow, WorkflowConfig, WorkflowStage, WorkflowStatistics } from './types'
import { DEFAULT_WORKFLOW_CONFIG } from './types'
import { v4Service, nowISO } from './utils'
import { canTransition, isTerminal } from './workflow-state'
import { workflowQueueService } from './workflow-queue'
import { checkpointService } from './checkpoint-service'
import { recoveryService } from './recovery-service'
import { retryService } from './retry-service'
import { auditService } from './audit-service'

const PREFIX = 'ajapp_ork_'

function get<T>(key: string, fallback: T): T { try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback } catch { return fallback } }
function set<T>(key: string, value: T): void { try { localStorage.setItem(key, JSON.stringify(value)) } catch {} }

export const workflowOrchestrator = {
  config: { ...DEFAULT_WORKFLOW_CONFIG },

  updateConfig(updates: Partial<WorkflowConfig>): void {
    this.config = { ...this.config, ...updates }
  },

  createWorkflow(jobTitle: string, companyName: string, matchScore: number, confidence: number, priority: number = 1): Workflow {
    const workflow: Workflow = {
      id: v4Service.generate('wf'),
      jobId: '',
      jobTitle,
      companyName,
      stage: 'discovered',
      status: 'running',
      executionMode: 'sequential',
      priority,
      matchScore,
      confidence,
      matchResultId: null,
      packageId: null,
      browserId: null,
      sessionId: null,
      applicationId: null,
      checkpoints: [],
      retryCount: 0,
      maxRetries: this.config.defaultMaxRetries,
      errors: [],
      audit: [],
      approval: null,
      metadata: {},
      createdAt: nowISO(),
      updatedAt: nowISO(),
      startedAt: nowISO(),
      completedAt: null,
    }

    const workflows = this.getAllWorkflows()
    workflows.unshift(workflow)
    set(`${PREFIX}workflows`, workflows.slice(0, 500))
    auditService.record(workflow.id, 'discovered', 'workflow_created', `Workflow created for ${jobTitle} at ${companyName}`, 'info', { matchScore, confidence })
    return workflow
  },

  transition(workflowId: string, to: WorkflowStage): boolean {
    const workflow = this.getWorkflow(workflowId)
    if (!workflow) return false
    if (!canTransition(workflow.stage, to)) return false

    workflow.stage = to
    workflow.updatedAt = nowISO()

    if (isTerminal(to)) {
      workflow.status = to as any
      workflow.completedAt = nowISO()
    }

    checkpointService.save(workflowId, to, { previousStage: workflow.stage })
    auditService.record(workflowId, to, 'stage_transition', `Transitioned to ${to}`, 'info')

    this.saveWorkflow(workflow)
    return true
  },

  getWorkflow(id: string): Workflow | undefined {
    return this.getAllWorkflows().find(w => w.id === id)
  },

  getAllWorkflows(): Workflow[] {
    return get<Workflow[]>(`${PREFIX}workflows`, [])
  },

  saveWorkflow(workflow: Workflow): void {
    const workflows = this.getAllWorkflows()
    const idx = workflows.findIndex(w => w.id === workflow.id)
    if (idx !== -1) workflows[idx] = workflow
    else workflows.unshift(workflow)
    set(`${PREFIX}workflows`, workflows.slice(0, 500))
  },

  deleteWorkflow(id: string): void {
    const workflows = this.getAllWorkflows().filter(w => w.id !== id)
    set(`${PREFIX}workflows`, workflows)
    checkpointService.clear(id)
    retryService.clearHistory(id)
    auditService.clear(id)
  },

  pauseWorkflow(id: string): void {
    const wf = this.getWorkflow(id)
    if (wf) { wf.status = 'paused'; wf.updatedAt = nowISO(); workflowQueueService.enqueue(id, 'paused', wf.priority, wf.stage, 'Workflow paused'); this.saveWorkflow(wf); auditService.record(id, wf.stage, 'workflow_paused', 'Workflow paused', 'info') }
  },

  resumeWorkflow(id: string): void {
    const wf = this.getWorkflow(id)
    if (wf) { wf.status = 'running'; wf.updatedAt = nowISO(); workflowQueueService.moveTo(id, 'paused', 'priority'); this.saveWorkflow(wf); auditService.record(id, wf.stage, 'workflow_resumed', 'Workflow resumed', 'info') }
  },

  cancelWorkflow(id: string): void {
    const wf = this.getWorkflow(id)
    if (wf) { this.transition(id, 'cancelled'); wf.completedAt = nowISO(); workflowQueueService.remove(id, 'priority'); workflowQueueService.remove(id, 'waiting'); workflowQueueService.remove(id, 'paused'); auditService.record(id, 'cancelled', 'workflow_cancelled', 'Workflow cancelled', 'warning') }
  },

  skipWorkflow(id: string): void {
    this.transition(id, 'skipped')
    auditService.record(id, 'skipped', 'workflow_skipped', 'Workflow skipped', 'info', { reason: 'Below threshold or user skipped' })
  },

  queueForProcessing(id: string): void {
    const wf = this.getWorkflow(id)
    if (wf) { workflowQueueService.enqueue(id, 'priority', wf.priority, wf.stage, 'Ready for processing'); this.transition(id, 'queued') }
  },

  async processQueue(): Promise<number> {
    let processed = 0
    let entry = workflowQueueService.peek('priority')
    while (entry && processed < this.config.maxConcurrency) {
      const wf = this.getWorkflow(entry.workflowId)
      if (wf) {
        const stage = entry.stage
        auditService.record(wf.id, stage, 'queue_processed', `Processing queued workflow at stage ${stage}`, 'info')
        processed++
      }
      workflowQueueService.dequeue('priority')
      entry = workflowQueueService.peek('priority')
    }
    return processed
  },

  async executeWithRetry(workflowId: string, action: () => Promise<boolean>): Promise<boolean> {
    const wf = this.getWorkflow(workflowId)
    if (!wf) return false

    for (let attempt = 0; attempt <= wf.maxRetries; attempt++) {
      try {
        const result = await action()
        if (result) {
          retryService.record(workflowId, wf.stage, 'Success', 0, true)
          return true
        }
        throw new Error('Action returned false')
      } catch (err) {
        wf.retryCount++
        const msg = err instanceof Error ? err.message : 'Unknown error'
        recoveryService.logError(wf, wf.stage, msg, 'ERR_EXECUTION', attempt < wf.maxRetries)
        const delay = retryService.computeDelay(attempt, this.config.retryBaseDelay, this.config.retryMaxDelay, this.config.backoffFactor)
        retryService.record(workflowId, wf.stage, msg, delay, false)
        auditService.record(workflowId, wf.stage, 'retry', `Attempt ${attempt + 1} failed: ${msg}`, 'warning', { attempt, maxRetries: wf.maxRetries })

        if (attempt < wf.maxRetries) {
          await new Promise(resolve => setTimeout(resolve, delay))
        } else {
          return false
        }
      }
    }
    return false
  },

  getStatistics(): WorkflowStatistics {
    const workflows = this.getAllWorkflows()
    const completed = workflows.filter(w => w.stage === 'completed')
    const failed = workflows.filter(w => w.stage === 'failed')
    const skipped = workflows.filter(w => w.stage === 'skipped')
    const scored = workflows.filter(w => w.matchScore > 0)
    const stageDist: Record<string, number> = {}
    for (const w of workflows) { stageDist[w.stage] = (stageDist[w.stage] || 0) + 1 }

    return {
      totalWorkflows: workflows.length,
      completedWorkflows: completed.length,
      failedWorkflows: failed.length,
      skippedWorkflows: skipped.length,
      averageMatchScore: scored.length > 0 ? Math.round((scored.reduce((s, w) => s + w.matchScore, 0) / scored.length) * 100) : 0,
      averageConfidence: scored.length > 0 ? Math.round(scored.reduce((s, w) => s + w.confidence, 0) / scored.length) : 0,
      successRate: workflows.length > 0 ? Math.round((completed.length / workflows.length) * 100) : 0,
      averageDuration: completed.length > 0 ? completed.reduce((s, w) => s + (w.completedAt && w.startedAt ? new Date(w.completedAt).getTime() - new Date(w.startedAt).getTime() : 0), 0) / completed.length : 0,
      totalRetries: retryService.getTotalRetries(),
      totalRecoveries: workflows.filter(w => w.errors.some(e => e.recovered)).length,
      stageDistribution: stageDist,
      dailyActivity: computeDailyActivity(workflows),
    }
  },

  getWorkflowsByStage(stage: WorkflowStage): Workflow[] {
    return this.getAllWorkflows().filter(w => w.stage === stage)
  },

  getRunningWorkflows(): Workflow[] {
    return this.getAllWorkflows().filter(w => w.status === 'running' && !isTerminal(w.stage))
  },
}

function computeDailyActivity(workflows: Workflow[]): { date: string; created: number; completed: number; failed: number }[] {
  const byDate = new Map<string, { created: number; completed: number; failed: number }>()
  for (const w of workflows) {
    const created = w.createdAt.split('T')[0]
    const completed = w.completedAt?.split('T')[0]
    if (!byDate.has(created)) byDate.set(created, { created: 0, completed: 0, failed: 0 })
    byDate.get(created)!.created++
    if (completed === created) byDate.get(created)!.completed++
    if (w.stage === 'failed' && completed) {
      if (!byDate.has(completed)) byDate.set(completed, { created: 0, completed: 0, failed: 0 })
      byDate.get(completed)!.failed++
    }
  }
  return Array.from(byDate.entries()).sort(([a], [b]) => a.localeCompare(b)).slice(-30).map(([date, counts]) => ({ date, ...counts }))
}
