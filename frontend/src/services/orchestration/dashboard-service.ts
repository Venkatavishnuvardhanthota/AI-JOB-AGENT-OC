import type { WorkflowDashboardData, WorkflowSummary } from './types'
import { workflowQueueService } from './workflow-queue'
import { auditService } from './audit-service'

const PREFIX = 'ajapp_ork_'

function get<T>(key: string, fallback: T): T { try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback } catch { return fallback } }
export const workflowDashboardService = {
  getDashboardData(): WorkflowDashboardData {
    const workflows = this.getAllActiveWorkflows()
    const queueSizes = workflowQueueService.totalSize()
    const recentActivity = auditService.getRecent(20)

    return {
      running: workflows.filter(w => w.status === 'running').length,
      queued: queueSizes.priority + queueSizes.waiting,
      paused: queueSizes.paused,
      completed: queueSizes.completed,
      failed: queueSizes.failed,
      totalRetries: queueSizes.retry,
      totalRecoveries: workflows.filter(w => w.errors.some(e => e.recovered)).length,
      pendingApprovals: workflows.filter(w => w.stage === 'awaiting_approval').length,
      workflows: workflows.slice(0, 50).map(w => this.toSummary(w)),
      recentActivity,
    }
  },

  getAllActiveWorkflows(): WorkflowType[] {
    return get<WorkflowType[]>(`${PREFIX}workflows`, [])
  },

  toSummary(wf: WorkflowType): WorkflowSummary {
    return {
      id: wf.id,
      jobTitle: wf.jobTitle,
      companyName: wf.companyName,
      stage: wf.stage as WorkflowSummary['stage'],
      status: wf.status as WorkflowSummary['status'],
      priority: wf.priority,
      matchScore: wf.matchScore,
      confidence: wf.confidence,
      progress: wf.checkpoints.map(c => ({ name: c.stage as any, status: 'completed' as const, startedAt: null, completedAt: null, duration: null, error: null })),
      createdAt: wf.createdAt,
      updatedAt: wf.updatedAt,
    }
  },
}

interface WorkflowType {
  id: string
  jobTitle: string
  companyName: string
  stage: string
  status: string
  priority: number
  matchScore: number
  confidence: number
  checkpoints: { stage: string }[]
  errors: { recovered: boolean }[]
  createdAt: string
  updatedAt: string
}
