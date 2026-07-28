import { describe, it, expect, beforeEach } from 'vitest'
import { canTransition, getAllowedTransitions, isTerminal, getStageLabel, getStageColor, getStageOrder } from './workflow-state'
import { workflowQueueService } from './workflow-queue'
import { approvalService } from './approval-service'
import { checkpointService } from './checkpoint-service'
import { recoveryService } from './recovery-service'
import { retryService } from './retry-service'
import { auditService } from './audit-service'
import { executionService } from './execution-service'
import { createPipelineStages, getStageProgress, updateStage } from './pipeline-service'
import { workflowOrchestrator } from './workflow-orchestrator'
import { workflowDashboardService } from './dashboard-service'


beforeEach(() => { localStorage.clear() })

describe('workflow-state', () => {
  it('allows valid transitions', () => {
    expect(canTransition('discovered', 'matched')).toBe(true)
    expect(canTransition('discovered', 'skipped')).toBe(true)
    expect(canTransition('discovered', 'completed')).toBe(false)
  })

  it('lists allowed transitions for a stage', () => {
    const transitions = getAllowedTransitions('generating')
    expect(transitions).toContain('generated')
    expect(transitions).toContain('failed')
  })

  it('identifies terminal states', () => {
    expect(isTerminal('completed')).toBe(true)
    expect(isTerminal('skipped')).toBe(true)
    expect(isTerminal('cancelled')).toBe(true)
    expect(isTerminal('failed')).toBe(false)
  })

  it('provides human-readable labels', () => {
    expect(getStageLabel('waiting_browser')).toBe('Waiting for Browser')
    expect(getStageLabel('form_detection')).toBe('Detecting Form')
    expect(getStageLabel('awaiting_approval')).toBe('Awaiting Approval')
  })

  it('provides stage colors', () => {
    expect(getStageColor('completed')).toBe('success')
    expect(getStageColor('failed')).toBe('destructive')
    expect(getStageColor('awaiting_approval')).toBe('warning')
  })

  it('orders stages correctly', () => {
    expect(getStageOrder('discovered')).toBeLessThan(getStageOrder('completed'))
  })
})

describe('workflow-queue', () => {
  it('enqueues workflow entries', () => {
    workflowQueueService.enqueue('wf1', 'priority', 1, 'queued')
    expect(workflowQueueService.size('priority')).toBe(1)
  })

  it('dequeues entries in priority order', () => {
    workflowQueueService.enqueue('wf1', 'priority', 1, 'queued')
    workflowQueueService.enqueue('wf2', 'priority', 5, 'queued')
    const first = workflowQueueService.dequeue('priority')
    expect(first?.workflowId).toBe('wf2')
  })

  it('peeks at next entry without removing', () => {
    workflowQueueService.enqueue('wf1', 'priority', 1, 'queued')
    expect(workflowQueueService.peek('priority')?.workflowId).toBe('wf1')
    expect(workflowQueueService.size('priority')).toBe(1)
  })

  it('removes entries from queue', () => {
    workflowQueueService.enqueue('wf1', 'priority', 1, 'queued')
    workflowQueueService.remove('wf1', 'priority')
    expect(workflowQueueService.size('priority')).toBe(0)
  })

  it('moves entries between queues', () => {
    workflowQueueService.enqueue('wf1', 'priority', 1, 'queued')
    workflowQueueService.moveTo('wf1', 'priority', 'paused', 'Test pause')
    expect(workflowQueueService.size('priority')).toBe(0)
    expect(workflowQueueService.size('paused')).toBe(1)
  })

  it('updates priority', () => {
    workflowQueueService.enqueue('wf1', 'priority', 1, 'queued')
    workflowQueueService.updatePriority('wf1', 'priority', 10)
    expect(workflowQueueService.peek('priority')?.priority).toBe(10)
  })

  it('reports total queue sizes', () => {
    workflowQueueService.enqueue('wf1', 'priority', 1, 'queued')
    workflowQueueService.enqueue('wf2', 'retry', 1, 'retrying')
    const sizes = workflowQueueService.totalSize()
    expect(sizes.priority).toBe(1)
    expect(sizes.retry).toBe(1)
  })

  it('clears individual queues', () => {
    workflowQueueService.enqueue('wf1', 'priority', 1, 'queued')
    workflowQueueService.clearQueue('priority')
    expect(workflowQueueService.size('priority')).toBe(0)
  })
})

describe('approval-service', () => {
  it('requests approval', () => {
    const entry = approvalService.requestApproval('wf1')
    expect(entry.status).toBe('pending')
    expect(entry.workflowId).toBe('wf1')
  })

  it('approves pending requests', () => {
    const entry = approvalService.requestApproval('wf1')
    const approved = approvalService.approve(entry.id, 'test_user', 'Looks good')
    expect(approved?.status).toBe('approved')
    expect(approved?.decidedBy).toBe('test_user')
  })

  it('rejects pending requests', () => {
    const entry = approvalService.requestApproval('wf1')
    const rejected = approvalService.reject(entry.id, 'test_user', 'Not ready')
    expect(rejected?.status).toBe('rejected')
  })

  it('lists pending approvals', () => {
    approvalService.requestApproval('wf1')
    approvalService.requestApproval('wf2')
    const approved = approvalService.requestApproval('wf3')
    approvalService.approve(approved.id, 'user')
    expect(approvalService.getPendingApprovals()).toHaveLength(2)
  })
})

describe('checkpoint-service', () => {
  it('saves and retrieves checkpoints', () => {
    const cp = checkpointService.save('wf1', 'navigating', { url: 'https://example.com' })
    expect(cp.stage).toBe('navigating')
    expect(cp.data.url).toBe('https://example.com')
  })

  it('gets latest checkpoint', () => {
    checkpointService.save('wf1', 'discovered')
    checkpointService.save('wf1', 'matched')
    const latest = checkpointService.getLatest('wf1')
    expect(latest?.stage).toBe('matched')
  })

  it('restores checkpoint', () => {
    const cp = checkpointService.save('wf1', 'filling', { formData: {} })
    const restored = checkpointService.restore('wf1', cp.id)
    expect(restored?.restored).toBe(true)
  })
})

describe('recovery-service', () => {
  it('determines if recovery is possible', () => {
    const wf = workflowOrchestrator.createWorkflow('Engineer', 'Co', 0.8, 70)
    wf.maxRetries = 3
    expect(recoveryService.canRecover(wf)).toBe(true)
  })

  it('prevents recovery when retries exhausted', () => {
    const wf = workflowOrchestrator.createWorkflow('Engineer', 'Co', 0.8, 70)
    wf.retryCount = 5
    wf.maxRetries = 3
    expect(recoveryService.canRecover(wf)).toBe(false)
  })

  it('logs errors', () => {
    const wf = workflowOrchestrator.createWorkflow('Engineer', 'Co', 0.8, 70)
    recoveryService.logError(wf, 'navigating', 'Navigation timeout', 'ERR_TIMEOUT')
    expect(wf.errors).toHaveLength(1)
    expect(wf.errors[0].code).toBe('ERR_TIMEOUT')
    expect(wf.errors[0].retryable).toBe(true)
  })
})

describe('retry-service', () => {
  it('determines if retry is needed', () => {
    expect(retryService.shouldRetry(0, 3)).toBe(true)
    expect(retryService.shouldRetry(3, 3)).toBe(false)
  })

  it('computes exponential backoff delay', () => {
    const delay = retryService.computeDelay(0, 1000, 30000, 2)
    expect(delay).toBe(1000)
    expect(retryService.computeDelay(3, 1000, 30000, 2)).toBe(8000)
  })

  it('records retry history', () => {
    retryService.record('wf1', 'navigating', 'Timeout', 1000, false)
    retryService.record('wf1', 'navigating', 'Success', 0, true)
    expect(retryService.getHistory('wf1')).toHaveLength(2)
    expect(retryService.getHistory('wf1')[0].success).toBe(false)
    expect(retryService.getHistory('wf1')[1].success).toBe(true)
  })

  it('provides retry analytics', () => {
    retryService.record('wf1', 'navigating', 'Fail', 1000, false)
    retryService.record('wf1', 'navigating', 'Success', 0, true)
    const analytics = retryService.getRetryAnalytics()
    expect(analytics.totalRetries).toBe(2)
    expect(analytics.successRate).toBe(50)
  })
})

describe('audit-service', () => {
  it('records audit entries', () => {
    auditService.record('wf1', 'discovered', 'workflow_created', 'Workflow created', 'info')
    expect(auditService.getEntries('wf1')).toHaveLength(1)
  })

  it('searches audit entries', () => {
    auditService.record('wf1', 'discovered', 'workflow_created', 'Workflow created for Senior Engineer', 'info')
    auditService.record('wf2', 'completed', 'workflow_completed', 'Application submitted successfully', 'info')
    const results = auditService.search('Senior')
    expect(results).toHaveLength(1)
    expect(results[0].message).toContain('Senior')
  })

  it('gets recent entries across workflows', () => {
    auditService.record('wf1', 'discovered', 'created', 'First', 'info')
    auditService.record('wf2', 'completed', 'done', 'Second', 'info')
    expect(auditService.getRecent(5)).toHaveLength(2)
  })
})

describe('execution-service', () => {
  it('executes workflows sequentially', async () => {
    const workflows = [{ id: '1' }, { id: '2' }] as any[]
    let count = 0
    const result = await executionService.executeSequential(workflows, async () => { count++; return true })
    expect(result.success).toBe(2)
    expect(count).toBe(2)
  })

  it('executes workflows in parallel', async () => {
    const workflows = [{ id: '1' }, { id: '2' }, { id: '3' }] as any[]
    const result = await executionService.executeParallel(workflows, async () => true, 2)
    expect(result.success).toBe(3)
  })
})

describe('pipeline-service', () => {
  it('creates pipeline stages', () => {
    const stages = createPipelineStages()
    expect(stages.length).toBeGreaterThan(5)
    expect(stages[0].status).toBe('pending')
  })

  it('updates stage status', () => {
    const stages = createPipelineStages()
    const updated = updateStage(stages, 'discovered', { status: 'completed' })
    expect(updated[0].status).toBe('completed')
  })

  it('calculates stage progress', () => {
    let stages = createPipelineStages()
    stages = updateStage(stages, 'discovered', { status: 'completed' })
    stages = updateStage(stages, 'matched', { status: 'completed' })
    const progress = getStageProgress(stages)
    expect(progress.completed).toBe(2)
    expect(progress.total).toBe(11)
  })
})

describe('workflow-orchestrator', () => {
  it('creates a workflow', () => {
    const wf = workflowOrchestrator.createWorkflow('Engineer', 'Company', 0.85, 75, 1)
    expect(wf.id).toMatch(/^wf_/)
    expect(wf.jobTitle).toBe('Engineer')
    expect(wf.stage).toBe('discovered')
    expect(wf.matchScore).toBe(0.85)
    expect(wf.confidence).toBe(75)
  })

  it('transitions between valid stages', () => {
    const wf = workflowOrchestrator.createWorkflow('Engineer', 'Company', 0.8, 70)
    expect(workflowOrchestrator.transition(wf.id, 'matched')).toBe(true)
    expect(workflowOrchestrator.getWorkflow(wf.id)?.stage).toBe('matched')
  })

  it('rejects invalid transitions', () => {
    const wf = workflowOrchestrator.createWorkflow('Engineer', 'Company', 0.8, 70)
    expect(workflowOrchestrator.transition(wf.id, 'completed')).toBe(false)
  })

  it('lists all workflows', () => {
    workflowOrchestrator.createWorkflow('Engineer', 'Co', 0.8, 70)
    workflowOrchestrator.createWorkflow('Designer', 'Co', 0.7, 60)
    expect(workflowOrchestrator.getAllWorkflows()).toHaveLength(2)
  })

  it('pauses and resumes workflows', () => {
    const wf = workflowOrchestrator.createWorkflow('Engineer', 'Co', 0.8, 70)
    workflowOrchestrator.pauseWorkflow(wf.id)
    expect(workflowOrchestrator.getWorkflow(wf.id)?.status).toBe('paused')
    workflowOrchestrator.resumeWorkflow(wf.id)
    expect(workflowOrchestrator.getWorkflow(wf.id)?.status).toBe('running')
  })

  it('cancels workflows', () => {
    const wf = workflowOrchestrator.createWorkflow('Engineer', 'Co', 0.8, 70)
    workflowOrchestrator.cancelWorkflow(wf.id)
    expect(workflowOrchestrator.getWorkflow(wf.id)?.stage).toBe('cancelled')
  })

  it('skips workflows', () => {
    const wf = workflowOrchestrator.createWorkflow('Engineer', 'Co', 0.8, 70)
    workflowOrchestrator.skipWorkflow(wf.id)
    expect(workflowOrchestrator.getWorkflow(wf.id)?.stage).toBe('skipped')
  })

  it('deletes workflows', () => {
    const wf = workflowOrchestrator.createWorkflow('Engineer', 'Co', 0.8, 70)
    workflowOrchestrator.deleteWorkflow(wf.id)
    expect(workflowOrchestrator.getWorkflow(wf.id)).toBeUndefined()
  })

  it('queues workflow for processing', () => {
    const wf = workflowOrchestrator.createWorkflow('Engineer', 'Co', 0.8, 70)
    workflowOrchestrator.transition(wf.id, 'matched')
    workflowOrchestrator.queueForProcessing(wf.id)
    expect(workflowOrchestrator.getWorkflow(wf.id)?.stage).toBe('queued')
  })

  it('computes statistics', () => {
    workflowOrchestrator.createWorkflow('Engineer', 'CoA', 0.9, 80)
    workflowOrchestrator.createWorkflow('Designer', 'CoB', 0.7, 60)
    const stats = workflowOrchestrator.getStatistics()
    expect(stats.totalWorkflows).toBe(2)
    expect(stats.averageMatchScore).toBeGreaterThan(0)
  })

  it('gets running workflows', () => {
    const wf = workflowOrchestrator.createWorkflow('Engineer', 'Co', 0.8, 70)
    workflowOrchestrator.transition(wf.id, 'matched')
    expect(workflowOrchestrator.getRunningWorkflows()).toHaveLength(1)
  })

  it('gets workflows by stage', () => {
    const wf = workflowOrchestrator.createWorkflow('Engineer', 'Co', 0.8, 70)
    workflowOrchestrator.transition(wf.id, 'matched')
    expect(workflowOrchestrator.getWorkflowsByStage('matched')).toHaveLength(1)
  })

  it('allows config updates', () => {
    workflowOrchestrator.updateConfig({ matchThreshold: 0.7, maxConcurrency: 5 })
    expect(workflowOrchestrator.config.matchThreshold).toBe(0.7)
    expect(workflowOrchestrator.config.maxConcurrency).toBe(5)
  })
})

describe('dashboard-service', () => {
  it('provides dashboard data', () => {
    localStorage.clear()
    workflowOrchestrator.createWorkflow('Engineer', 'Co', 0.8, 70)
    const data = workflowDashboardService.getDashboardData()
    expect(data.workflows.length).toBeGreaterThan(0)
    expect(data.running).toBe(1)
    expect(data.queued).toBe(0)
  })
})
