import { useMemo } from 'react'

export interface ApplicationAge {
  label: string
  days: number
  isStale: boolean
  staleReason?: string
}

export function getApplicationAge(dateStr: string): ApplicationAge {
  const now = Date.now()
  const date = new Date(dateStr).getTime()
  const diffMs = now - date
  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  let label: string
  if (days === 0) label = 'Today'
  else if (days === 1) label = '1 day'
  else if (days < 7) label = `${days} days`
  else if (days < 30) {
    const weeks = Math.floor(days / 7)
    label = `${weeks} week${weeks > 1 ? 's' : ''}`
  } else if (days < 90) {
    const months = Math.floor(days / 30)
    label = `${months} month${months > 1 ? 's' : ''}`
  } else label = `${Math.floor(days / 30)} months`

  let isStale = false
  let staleReason: string | undefined
  if (days >= 90) { isStale = true; staleReason = 'No activity for 90+ days' }
  else if (days >= 45) { isStale = true; staleReason = 'No activity for 45+ days' }
  else if (days >= 30) { isStale = true; staleReason = 'No activity for 30+ days' }

  return { label, days, isStale, staleReason }
}

export function useApplicationAge(dateStr: string) {
  return useMemo(() => getApplicationAge(dateStr), [dateStr])
}

export function useNoActivityDays(updatedAt: string): ApplicationAge {
  return useMemo(() => getApplicationAge(updatedAt), [updatedAt])
}
