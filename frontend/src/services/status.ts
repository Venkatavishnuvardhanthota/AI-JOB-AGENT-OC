import type { ApplicationStatus } from '@/types'

export const APPLICATION_STATUSES: ApplicationStatus[] = [
  'saved',
  'preparing',
  'ready_to_apply',
  'applied',
  'application_viewed',
  'assessment',
  'technical_interview',
  'hr_interview',
  'final_interview',
  'offer',
  'negotiation',
  'accepted',
  'rejected',
  'withdrawn',
  'archived',
]

const STATUS_FLOW: Record<ApplicationStatus, ApplicationStatus[]> = {
  saved: ['preparing', 'archived'],
  preparing: ['ready_to_apply', 'saved', 'withdrawn'],
  ready_to_apply: ['applied', 'preparing', 'withdrawn'],
  applied: ['application_viewed', 'assessment', 'rejected', 'withdrawn'],
  application_viewed: ['assessment', 'technical_interview', 'rejected'],
  assessment: ['technical_interview', 'hr_interview', 'rejected', 'withdrawn'],
  technical_interview: ['hr_interview', 'final_interview', 'rejected', 'withdrawn'],
  hr_interview: ['final_interview', 'technical_interview', 'rejected', 'withdrawn'],
  final_interview: ['offer', 'hr_interview', 'rejected', 'withdrawn'],
  offer: ['negotiation', 'accepted', 'rejected', 'withdrawn'],
  negotiation: ['accepted', 'offer', 'rejected', 'withdrawn'],
  accepted: ['archived'],
  rejected: ['archived', 'applied'],
  withdrawn: ['archived'],
  archived: [],
}

export function getAllowedTransitions(status: ApplicationStatus): ApplicationStatus[] {
  return STATUS_FLOW[status] || []
}

export function canTransition(from: ApplicationStatus, to: ApplicationStatus): boolean {
  return getAllowedTransitions(from).includes(to)
}

export function getStatusLabel(status: ApplicationStatus): string {
  const labels: Record<ApplicationStatus, string> = {
    saved: 'Saved',
    preparing: 'Preparing',
    ready_to_apply: 'Ready To Apply',
    applied: 'Applied',
    application_viewed: 'Application Viewed',
    assessment: 'Assessment',
    technical_interview: 'Technical Interview',
    hr_interview: 'HR Interview',
    final_interview: 'Final Interview',
    offer: 'Offer',
    negotiation: 'Negotiation',
    accepted: 'Accepted',
    rejected: 'Rejected',
    withdrawn: 'Withdrawn',
    archived: 'Archived',
  }
  return labels[status]
}

export function getStatusCategory(status: ApplicationStatus): 'active' | 'preparation' | 'interview' | 'offer' | 'final' {
  const active: ApplicationStatus[] = ['applied', 'application_viewed']
  const preparation: ApplicationStatus[] = ['saved', 'preparing', 'ready_to_apply']
  const interview: ApplicationStatus[] = ['assessment', 'technical_interview', 'hr_interview', 'final_interview']
  const offer: ApplicationStatus[] = ['offer', 'negotiation']

  if (active.includes(status)) return 'active'
  if (preparation.includes(status)) return 'preparation'
  if (interview.includes(status)) return 'interview'
  if (offer.includes(status)) return 'offer'
  return 'final'
}

export const STATUS_ORDER: Record<number, ApplicationStatus> = {
  0: 'saved',
  1: 'preparing',
  2: 'ready_to_apply',
  3: 'applied',
  4: 'application_viewed',
  5: 'assessment',
  6: 'technical_interview',
  7: 'hr_interview',
  8: 'final_interview',
  9: 'offer',
  10: 'negotiation',
  11: 'accepted',
  12: 'rejected',
  13: 'withdrawn',
  14: 'archived',
}

export const PRIORITY_LABELS: Record<string, string> = {
  critical: 'Critical',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
}

export const PRIORITY_ORDER: string[] = ['critical', 'high', 'medium', 'low']
