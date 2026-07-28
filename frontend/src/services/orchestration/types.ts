export type WorkflowStage =
  | 'discovered' | 'matched' | 'generating' | 'generated'
  | 'queued' | 'waiting_browser' | 'navigating' | 'form_detection'
  | 'filling' | 'uploading' | 'review' | 'awaiting_approval'
  | 'submitting' | 'submitted' | 'tracking' | 'completed'
  | 'skipped' | 'cancelled' | 'failed' | 'recovered' | 'retrying'

export type QueueType = 'priority' | 'retry' | 'paused' | 'waiting' | 'completed' | 'failed' | 'cancelled'
export type ExecutionMode = 'sequential' | 'parallel'
export type ApprovalStatus = 'pending' | 'approved' | 'rejected' | 'changes_requested'
export type AuditSeverity = 'info' | 'warning' | 'error' | 'critical'

export const VALID_TRANSITIONS: Record<WorkflowStage, WorkflowStage[]> = {
  discovered: ['matched', 'skipped', 'cancelled'],
  matched: ['generating', 'queued', 'skipped', 'cancelled'],
  generating: ['generated', 'failed', 'cancelled'],
  generated: ['queued', 'awaiting_approval', 'skipped', 'cancelled'],
  queued: ['waiting_browser', 'cancelled'],
  waiting_browser: ['navigating', 'failed', 'retrying', 'cancelled'],
  navigating: ['form_detection', 'failed', 'retrying', 'cancelled'],
  form_detection: ['filling', 'failed', 'retrying', 'cancelled'],
  filling: ['uploading', 'review', 'failed', 'retrying', 'cancelled'],
  uploading: ['review', 'failed', 'retrying', 'cancelled'],
  review: ['awaiting_approval', 'submitting', 'failed', 'cancelled'],
  awaiting_approval: ['submitting', 'filling', 'generating', 'cancelled', 'retrying'],
  submitting: ['submitted', 'failed', 'retrying', 'cancelled'],
  submitted: ['tracking', 'completed', 'failed', 'cancelled'],
  tracking: ['completed', 'failed', 'retrying', 'cancelled'],
  completed: [],
  skipped: [],
  cancelled: [],
  failed: ['recovered', 'retrying'],
  recovered: ['waiting_browser', 'navigating', 'filling', 'submitting', 'queued'],
  retrying: ['waiting_browser', 'navigating', 'filling', 'uploading', 'submitting', 'failed'],
}

export interface Workflow {
  id: string
  jobId: string
  jobTitle: string
  companyName: string
  stage: WorkflowStage
  status: 'running' | 'paused' | 'completed' | 'failed' | 'cancelled'
  executionMode: ExecutionMode
  priority: number
  matchScore: number
  confidence: number
  matchResultId: string | null
  packageId: string | null
  browserId: string | null
  sessionId: string | null
  applicationId: string | null
  checkpoints: Checkpoint[]
  retryCount: number
  maxRetries: number
  errors: WorkflowError[]
  audit: AuditEntry[]
  approval: ApprovalEntry | null
  metadata: Record<string, unknown>
  createdAt: string
  updatedAt: string
  startedAt: string | null
  completedAt: string | null
}

export interface Checkpoint {
  id: string
  stage: WorkflowStage
  timestamp: string
  data: Record<string, unknown>
  restored: boolean
}

export interface WorkflowError {
  stage: WorkflowStage
  message: string
  code: string
  timestamp: string
  retryable: boolean
  recovered: boolean
}

export interface QueueEntry {
  workflowId: string
  queueType: QueueType
  priority: number
  stage: WorkflowStage
  enqueuedAt: string
  retryCount: number
  reason: string | null
}

export interface ApprovalEntry {
  id: string
  workflowId: string
  status: ApprovalStatus
  requestedAt: string
  decidedAt: string | null
  decidedBy: string | null
  comment: string | null
  changes: string[]
}

export interface AuditEntry {
  id: string
  workflowId: string
  stage: WorkflowStage
  action: string
  severity: AuditSeverity
  message: string
  data: Record<string, unknown> | null
  timestamp: string
}

export interface RetryRecord {
  attempt: number
  stage: WorkflowStage
  reason: string
  delay: number
  timestamp: string
  success: boolean
}

export interface WorkflowConfig {
  matchThreshold: number
  confidenceThreshold: number
  requireApproval: boolean
  maxConcurrency: number
  defaultMaxRetries: number
  retryBaseDelay: number
  retryMaxDelay: number
  backoffFactor: number
  browserProvider: string
  browserHeadless: boolean
  includeCoverLetter: boolean
  autoSubmit: boolean
  queuePollInterval: number
}

export const DEFAULT_WORKFLOW_CONFIG: WorkflowConfig = {
  matchThreshold: 0.6,
  confidenceThreshold: 60,
  requireApproval: false,
  maxConcurrency: 3,
  defaultMaxRetries: 3,
  retryBaseDelay: 1000,
  retryMaxDelay: 30000,
  backoffFactor: 2,
  browserProvider: 'chromium',
  browserHeadless: true,
  includeCoverLetter: true,
  autoSubmit: true,
  queuePollInterval: 5000,
}

export interface PipelineStage {
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped'
  startedAt: string | null
  completedAt: string | null
  duration: number | null
  error: string | null
}

export interface WorkflowDashboardData {
  running: number
  queued: number
  paused: number
  completed: number
  failed: number
  totalRetries: number
  totalRecoveries: number
  pendingApprovals: number
  workflows: WorkflowSummary[]
  recentActivity: AuditEntry[]
}

export interface WorkflowSummary {
  id: string
  jobTitle: string
  companyName: string
  stage: WorkflowStage
  status: string
  priority: number
  matchScore: number
  confidence: number
  progress: PipelineStage[]
  createdAt: string
  updatedAt: string
}

export interface WorkflowStatistics {
  totalWorkflows: number
  completedWorkflows: number
  failedWorkflows: number
  skippedWorkflows: number
  averageMatchScore: number
  averageConfidence: number
  successRate: number
  averageDuration: number
  totalRetries: number
  totalRecoveries: number
  stageDistribution: Record<string, number>
  dailyActivity: { date: string; created: number; completed: number; failed: number }[]
}
