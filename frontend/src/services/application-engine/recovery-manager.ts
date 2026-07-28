import type { Checkpoint, FormEngineState } from './types'
import { checkpointService } from './checkpoints'

export const recoveryManager = {
  canRecover(workflowId: string): boolean {
    const latest = checkpointService.getLatest(workflowId)
    return latest !== null
  },

  getRecoveryPlan(workflowId: string): { canRecover: boolean; checkpoint: Checkpoint | null; nextState: FormEngineState } {
    const latest = checkpointService.getLatest(workflowId)

    if (!latest) {
      return { canRecover: false, checkpoint: null, nextState: 'idle' }
    }

    let nextState: FormEngineState = 'detecting'

    switch (latest.lastAction) {
      case 'navigate':
        nextState = 'navigating'
        break
      case 'detect':
        nextState = 'detecting'
        break
      case 'map':
        nextState = 'mapping'
        break
      case 'fill':
        nextState = 'filling'
        break
      case 'upload':
        nextState = 'uploading'
        break
      case 'generate_ai':
        nextState = 'ai_generating'
        break
      case 'submit':
        nextState = 'submitting'
        break
      default:
        nextState = 'filling'
    }

    return { canRecover: true, checkpoint: latest, nextState }
  },

  recoverState(workflowId: string): Partial<Record<string, unknown>> {
    const plan = this.getRecoveryPlan(workflowId)
    if (!plan.canRecover || !plan.checkpoint) return {}

    return {
      stepIndex: plan.checkpoint.stepIndex,
      completedFields: plan.checkpoint.completedFields,
      fieldValues: plan.checkpoint.fieldValues,
      uploadedDocuments: plan.checkpoint.uploadedDocuments,
      applicationUrl: plan.checkpoint.applicationUrl,
      providerId: plan.checkpoint.providerId,
    }
  },

  getIncompleteFields(checkpoint: Checkpoint, allFieldIds: string[]): string[] {
    return allFieldIds.filter(id => !checkpoint.completedFields.includes(id))
  },
}
