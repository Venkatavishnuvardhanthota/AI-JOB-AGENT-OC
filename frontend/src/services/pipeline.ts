import { applicationService } from './application'
import { canTransition } from './status'
import type { Application, ApplicationStatus } from '@/types'

export type GroupBy = 'none' | 'company' | 'priority' | 'recruiter' | 'location' | 'source' | 'work_type'

export const GROUP_BY_OPTIONS: { value: GroupBy; label: string }[] = [
  { value: 'none', label: 'Standard' },
  { value: 'company', label: 'Company' },
  { value: 'priority', label: 'Priority' },
  { value: 'recruiter', label: 'Recruiter' },
  { value: 'location', label: 'Location' },
  { value: 'source', label: 'Source' },
  { value: 'work_type', label: 'Work Type' },
]

export function getGroupKey(application: Application, groupBy: GroupBy): string {
  switch (groupBy) {
    case 'company': return application.company_name || 'Unknown Company'
    case 'priority': return application.priority || 'none'
    case 'recruiter': return application.recruiter || 'No Recruiter'
    case 'location': return application.location || 'No Location'
    case 'source': return application.source || 'Direct'
    case 'work_type': return application.work_type || 'Not Specified'
    default: return 'all'
  }
}

export interface MoveResult {
  success: boolean
  applicationId: string
  fromStatus: ApplicationStatus
  toStatus: ApplicationStatus
  error?: string
}

export async function moveApplication(
  applicationId: string,
  fromStatus: ApplicationStatus,
  toStatus: ApplicationStatus,
): Promise<MoveResult> {
  if (!canTransition(fromStatus, toStatus)) {
    return {
      success: false,
      applicationId,
      fromStatus,
      toStatus,
      error: `Cannot move from "${fromStatus}" to "${toStatus}". Invalid transition.`,
    }
  }

  try {
    await applicationService.updateStatus(applicationId, toStatus)
    return { success: true, applicationId, fromStatus, toStatus }
  } catch (err: any) {
    return {
      success: false,
      applicationId,
      fromStatus,
      toStatus,
      error: err?.message || 'Failed to update application status.',
    }
  }
}

export interface BulkMoveResult {
  successCount: number
  failCount: number
  errors: MoveResult[]
}

export async function bulkMoveApplications(
  applicationIds: string[],
  toStatus: ApplicationStatus,
): Promise<BulkMoveResult> {
  const results: MoveResult[] = []
  for (const id of applicationIds) {
    const app = await applicationService.get(id)
    const result = await moveApplication(id, app.status, toStatus)
    results.push(result)
  }
  return {
    successCount: results.filter(r => r.success).length,
    failCount: results.filter(r => !r.success).length,
    errors: results.filter(r => !r.success),
  }
}

export function getColumnValidation(applications: Application[], _status: ApplicationStatus): ColumnValidation {
  const highPriority = applications.filter(a => a.priority === 'critical' || a.priority === 'high')
  const overdue = applications.filter(a => a.deadline && new Date(a.deadline) < new Date())
  const interviewsScheduled = applications.filter(a =>
    ['technical_interview', 'hr_interview', 'final_interview'].includes(a.status)
  )
  const offers = applications.filter(a => a.status === 'offer' || a.status === 'negotiation')

  return {
    total: applications.length,
    highPriority: highPriority.length,
    overdue: overdue.length,
    interviewsScheduled: interviewsScheduled.length,
    offers: offers.length,
  }
}

export interface ColumnValidation {
  total: number
  highPriority: number
  overdue: number
  interviewsScheduled: number
  offers: number
}

export interface ColumnRule {
  id: string
  column: ApplicationStatus
  type: 'max_count' | 'overdue_warning' | 'expired_offer' | 'missing_document'
  threshold?: number
  enabled: boolean
  severity: 'info' | 'warning' | 'critical'
}

export function evaluateColumnRule(rule: ColumnRule, applications: Application[], validation: ColumnValidation): ColumnRuleResult | null {
  switch (rule.type) {
    case 'max_count': {
      const threshold = rule.threshold ?? 25
      if (validation.total > threshold) {
        return { rule, triggered: true, message: `Column has ${validation.total} applications (limit: ${threshold})`, severity: 'warning' }
      }
      return null
    }
    case 'overdue_warning': {
      if (validation.overdue > 0) {
        return { rule, triggered: true, message: `${validation.overdue} overdue follow-up${validation.overdue > 1 ? 's' : ''}`, severity: 'warning' }
      }
      return null
    }
    case 'expired_offer': {
      if (validation.offers > 0) {
        const expired = applications.filter(a => (a.status === 'offer' || a.status === 'negotiation') && a.deadline && new Date(a.deadline) < new Date())
        if (expired.length > 0) {
          return { rule, triggered: true, message: `${expired.length} expired offer${expired.length > 1 ? 's' : ''}`, severity: 'critical' }
        }
      }
      return null
    }
    case 'missing_document': {
      const missing = applications.filter(a => !a.resume_id)
      if (missing.length > 0) {
        return { rule, triggered: true, message: `${missing.length} application${missing.length > 1 ? 's' : ''} missing resume`, severity: 'info' }
      }
      return null
    }
    default:
      return null
  }
}

export interface ColumnRuleResult {
  rule: ColumnRule
  triggered: boolean
  message: string
  severity: 'info' | 'warning' | 'critical'
}

export const DEFAULT_COLUMN_RULES: ColumnRule[] = [
  { id: 'rule_applied_count', column: 'applied', type: 'max_count', threshold: 25, enabled: true, severity: 'warning' },
  { id: 'rule_interview_overdue', column: 'technical_interview', type: 'overdue_warning', enabled: true, severity: 'warning' },
  { id: 'rule_interview_hr_overdue', column: 'hr_interview', type: 'overdue_warning', enabled: true, severity: 'warning' },
  { id: 'rule_offer_expired', column: 'offer', type: 'expired_offer', enabled: true, severity: 'critical' },
  { id: 'rule_ready_missing_doc', column: 'ready_to_apply', type: 'missing_document', enabled: true, severity: 'info' },
]
