import { useMemo } from 'react'
import type { Application, ApplicationStatus } from '@/types'

export interface ReminderBadge {
  type: 'follow_up' | 'interview_tomorrow' | 'deadline_today' | 'deadline_soon' | 'resume_missing' | 'cover_letter_missing' | 'priority_high' | 'stale'
  label: string
  variant: 'warning' | 'destructive' | 'secondary' | 'default'
}

function daysUntil(dateStr: string): number {
  const diff = new Date(dateStr).getTime() - Date.now()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

export function getReminderBadges(application: Application): ReminderBadge[] {
  const badges: ReminderBadge[] = []

  const daysSinceUpdate = Math.floor((Date.now() - new Date(application.updated_at).getTime()) / (1000 * 60 * 60 * 24))

  if (daysSinceUpdate >= 14 && application.status !== 'accepted' && application.status !== 'rejected' && application.status !== 'archived' && application.status !== 'withdrawn') {
    badges.push({ type: 'follow_up', label: 'Follow up needed', variant: 'warning' })
  }

  if (application.deadline) {
    const d = daysUntil(application.deadline)
    if (d === 0) badges.push({ type: 'deadline_today', label: 'Deadline today', variant: 'destructive' })
    else if (d <= 3 && d > 0) badges.push({ type: 'deadline_soon', label: `Deadline in ${d} days`, variant: 'warning' })
  }

  const interviewStatuses: ApplicationStatus[] = ['technical_interview', 'hr_interview', 'final_interview']
  if (interviewStatuses.includes(application.status) && application.deadline) {
    const d = daysUntil(application.deadline)
    if (d === 1) badges.push({ type: 'interview_tomorrow', label: 'Interview tomorrow', variant: 'default' })
  }

  if (!application.resume_id && application.status !== 'saved') {
    badges.push({ type: 'resume_missing', label: 'Resume missing', variant: 'secondary' })
  }
  if (!application.cover_letter_id && (application.status === 'ready_to_apply' || application.status === 'applied')) {
    badges.push({ type: 'cover_letter_missing', label: 'Cover letter missing', variant: 'secondary' })
  }

  if (application.priority === 'critical' || application.priority === 'high') {
    badges.push({ type: 'priority_high', label: `Priority: ${application.priority}`, variant: 'destructive' })
  }

  if (daysSinceUpdate >= 30) {
    badges.push({ type: 'stale', label: 'No activity', variant: 'secondary' })
  }

  return badges
}

export function useReminderBadges(application: Application): ReminderBadge[] {
  return useMemo(() => getReminderBadges(application), [application])
}
