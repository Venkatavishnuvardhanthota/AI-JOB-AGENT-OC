import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | null | undefined): string {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function timeAgo(date: string | null | undefined): string {
  if (!date) return ''
  const diff = Date.now() - new Date(date).getTime()
  const days = Math.floor(diff / 86400000)
  if (days < 1) return 'Today'
  if (days === 1) return 'Yesterday'
  if (days < 30) return `${days}d ago`
  return `${Math.floor(days / 30)}mo ago`
}

export function formatSalary(
  min: number | null | undefined,
  max: number | null | undefined,
  currency?: string | null,
  period?: string | null
): string {
  if (min == null && max == null) return '-'
  const cur = currency || 'USD'
  const per = period ? `/${period}` : ''
  if (min != null && max != null) return `${cur} ${min.toLocaleString()} - ${max.toLocaleString()}${per}`
  if (min != null) return `${cur} ${min.toLocaleString()}+${per}`
  return `${cur} ${max!.toLocaleString()} max${per}`
}

export function getScoreColor(score: number): string {
  if (score >= 80) return 'text-green-500'
  if (score >= 60) return 'text-yellow-500'
  return 'text-red-500'
}

export function getScoreBg(score: number): string {
  if (score >= 80) return 'bg-green-500/10 text-green-500'
  if (score >= 60) return 'bg-yellow-500/10 text-yellow-500'
  return 'bg-red-500/10 text-red-500'
}
