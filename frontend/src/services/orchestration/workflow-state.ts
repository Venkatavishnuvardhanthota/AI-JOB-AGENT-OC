import type { WorkflowStage } from './types'
import { VALID_TRANSITIONS } from './types'

export function canTransition(from: WorkflowStage, to: WorkflowStage): boolean {
  const allowed = VALID_TRANSITIONS[from]
  return allowed ? allowed.includes(to) : false
}

export function getAllowedTransitions(stage: WorkflowStage): WorkflowStage[] {
  return VALID_TRANSITIONS[stage] ?? []
}

export function isTerminal(stage: WorkflowStage): boolean {
  return ['completed', 'skipped', 'cancelled'].includes(stage)
}

export function isFailureState(stage: WorkflowStage): boolean {
  return stage === 'failed'
}

export function isActiveState(stage: WorkflowStage): boolean {
  return !isTerminal(stage) && !isFailureState(stage) && stage !== 'retrying'
}

export function getStageLabel(stage: WorkflowStage): string {
  const labels: Record<WorkflowStage, string> = {
    discovered: 'Discovered', matched: 'Matched', generating: 'Generating Documents',
    generated: 'Documents Generated', queued: 'Queued', waiting_browser: 'Waiting for Browser',
    navigating: 'Navigating', form_detection: 'Detecting Form', filling: 'Filling Form',
    uploading: 'Uploading Documents', review: 'Reviewing', awaiting_approval: 'Awaiting Approval',
    submitting: 'Submitting', submitted: 'Submitted', tracking: 'Tracking',
    completed: 'Completed', skipped: 'Skipped', cancelled: 'Cancelled',
    failed: 'Failed', recovered: 'Recovered', retrying: 'Retrying',
  }
  return labels[stage]
}

export function getStageOrder(stage: WorkflowStage): number {
  const order: Record<WorkflowStage, number> = {
    discovered: 1, matched: 2, generating: 3, generated: 4,
    queued: 5, waiting_browser: 6, navigating: 7, form_detection: 8,
    filling: 9, uploading: 10, review: 11, awaiting_approval: 12,
    submitting: 13, submitted: 14, tracking: 15, completed: 16,
    skipped: 0, cancelled: 0, failed: -1, recovered: -1, retrying: -2,
  }
  return order[stage]
}

export function getStageColor(stage: WorkflowStage): string {
  if (stage === 'completed') return 'success'
  if (stage === 'failed' || stage === 'cancelled') return 'destructive'
  if (stage === 'retrying' || stage === 'recovered') return 'warning'
  if (stage === 'awaiting_approval') return 'warning'
  if (stage === 'skipped') return 'secondary'
  return 'default'
}
