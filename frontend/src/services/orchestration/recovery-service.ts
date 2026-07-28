import type { Workflow, WorkflowError } from './types'
import { checkpointService } from './checkpoint-service'
import { workflowQueueService } from './workflow-queue'
import { nowISO } from './utils'

export const recoveryService = {
  canRecover(workflow: Workflow): boolean {
    if (workflow.retryCount >= workflow.maxRetries) return false
    const lastError = workflow.errors[workflow.errors.length - 1]
    return lastError ? lastError.retryable : true
  },

  getRecoveryStage(workflow: Workflow): { stage: string; data: Record<string, unknown> } | null {
    const checkpoint = checkpointService.getLatest(workflow.id)
    if (!checkpoint) return null
    const recoverableStages = ['waiting_browser', 'navigating', 'filling', 'uploading', 'submitting']
    if (recoverableStages.includes(checkpoint.stage)) {
      return { stage: checkpoint.stage, data: checkpoint.data }
    }
    return null
  },

  attemptRecovery(workflow: Workflow): { recovered: boolean; nextStage: string | null } {
    if (!this.canRecover(workflow)) return { recovered: false, nextStage: null }

    const recovery = this.getRecoveryStage(workflow)
    if (!recovery) return { recovered: false, nextStage: null }

    workflowQueueService.enqueue(workflow.id, 'retry', workflow.priority, recovery.stage as any, 'Recovery attempt')
    return { recovered: true, nextStage: recovery.stage }
  },

  logError(workflow: Workflow, stage: string, message: string, code: string = 'ERR_GENERIC', retryable: boolean = true): WorkflowError {
    const error: WorkflowError = {
      stage: stage as any,
      message,
      code,
      timestamp: nowISO(),
      retryable,
      recovered: false,
    }
    workflow.errors.push(error)
    workflow.updatedAt = nowISO()
    return error
  },

  markRecovered(workflow: Workflow, errorIdx: number): void {
    if (workflow.errors[errorIdx]) {
      workflow.errors[errorIdx].recovered = true
    }
  },
}
