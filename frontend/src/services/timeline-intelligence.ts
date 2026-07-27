import type { Application } from '@/types'

export interface BenchmarkMetric {
  label: string
  value: string
  previousValue?: string
  change?: number
  trend: 'positive' | 'negative' | 'neutral'
  description: string
}

export interface CohortPeriod {
  label: string
  applications: number
  interviews: number
  offers: number
  acceptances: number
  interviewRate: number
  offerRate: number
  acceptanceRate: number
}

export interface HeatMapData {
  weekday: string[]
  hourSlots: string[]
  data: number[][]
  maxValue: number
}

export function computeBenchmarkCards(applications: Application[]): BenchmarkMetric[] {
  const cards: BenchmarkMetric[] = []

  const applied = applications.filter(a => a.status !== 'saved' && a.status !== 'preparing' && a.status !== 'ready_to_apply')
  const responded = applied.filter(a => a.status !== 'applied' && a.status !== 'application_viewed')
  const interviews = applied.filter(a =>
    ['technical_interview', 'hr_interview', 'final_interview'].includes(a.status)
  )
  const offers = applied.filter(a =>
    ['offer', 'negotiation', 'accepted'].includes(a.status)
  )

  const responseRate = applied.length > 0 ? Math.round((responded.length / applied.length) * 100) : 0
  const interviewRate = applied.length > 0 ? Math.round((interviews.length / applied.length) * 100) : 0
  const offerRate = applied.length > 0 ? Math.round((offers.length / applied.length) * 100) : 0

  cards.push({
    label: 'Response Rate',
    value: `${responseRate}%`,
    trend: responseRate > 30 ? 'positive' : responseRate > 10 ? 'neutral' : 'negative',
    description: `${responded.length} of ${applied.length} applications received a response`,
  })

  cards.push({
    label: 'Interview Rate',
    value: `${interviewRate}%`,
    trend: interviewRate > 25 ? 'positive' : interviewRate > 10 ? 'neutral' : 'negative',
    description: `${interviews.length} interviews from ${applied.length} applications`,
  })

  cards.push({
    label: 'Offer Rate',
    value: `${offerRate}%`,
    trend: offerRate > 15 ? 'positive' : offerRate > 5 ? 'neutral' : 'negative',
    description: `${offers.length} offers from ${applied.length} applications`,
  })

  const half = Math.floor(applied.length / 2)
  if (half > 0) {
    const firstHalf = applied.slice(0, half)
    const secondHalf = applied.slice(half)

    const firstInt = firstHalf.filter(a => interviews.some(i => i.id === a.id)).length
    const secondInt = secondHalf.filter(a => interviews.some(i => i.id === a.id)).length
    const firstRate = firstHalf.length > 0 ? Math.round((firstInt / firstHalf.length) * 100) : 0
    const secondRate = secondHalf.length > 0 ? Math.round((secondInt / secondHalf.length) * 100) : 0
    const change = secondRate - firstRate

    if (firstHalf.length >= 3 && secondHalf.length >= 3) {
      cards.push({
        label: 'Interview Rate Trend',
        value: `${secondRate}%`,
        previousValue: `${firstRate}%`,
        change,
        trend: change > 0 ? 'positive' : change < 0 ? 'negative' : 'neutral',
        description: change > 0 ? `Improved from ${firstRate}%` : change < 0 ? `Declined from ${firstRate}%` : 'No change',
      })
    }
  }

  const avgResponseDays = computeAverageResponseTime(applications)
  if (avgResponseDays > 0) {
    cards.push({
      label: 'Avg Response Time',
      value: `${avgResponseDays} days`,
      trend: avgResponseDays <= 7 ? 'positive' : avgResponseDays <= 14 ? 'neutral' : 'negative',
      description: `Average time to receive a response`,
    })
  }

  const avgHiringDays = computeAverageHiringDuration(applications)
  if (avgHiringDays > 0) {
    cards.push({
      label: 'Avg Hiring Duration',
      value: `${avgHiringDays} days`,
      trend: avgHiringDays <= 30 ? 'positive' : avgHiringDays <= 60 ? 'neutral' : 'negative',
      description: `Average time from application to offer`,
    })
  }

  return cards
}

export function computeAverageResponseTime(applications: Application[]): number {
  const withUpdates = applications
    .filter(a => {
      const created = new Date(a.created_at).getTime()
      const updated = new Date(a.updated_at).getTime()
      return updated > created + 86400000
    })
    .map(a => Math.round((new Date(a.updated_at).getTime() - new Date(a.created_at).getTime()) / 86400000))

  if (withUpdates.length === 0) return 0
  return Math.round(withUpdates.reduce((a, b) => a + b, 0) / withUpdates.length)
}

export function computeAverageHiringDuration(applications: Application[]): number {
  const hired = applications.filter(a => a.status === 'accepted')
  if (hired.length === 0) return 0
  const durations = hired
    .map(a => Math.round((new Date(a.updated_at).getTime() - new Date(a.created_at).getTime()) / 86400000))
    .filter(d => d > 0)
  if (durations.length === 0) return 0
  return Math.round(durations.reduce((a, b) => a + b, 0) / durations.length)
}

export function computeFastestHiringProcess(applications: Application[]): { company: string; days: number } | null {
  const hired = applications.filter(a => a.status === 'accepted')
  if (hired.length === 0) return null
  let fastest = { company: '', days: Infinity }
  for (const app of hired) {
    const days = Math.round((new Date(app.updated_at).getTime() - new Date(app.created_at).getTime()) / 86400000)
    if (days > 0 && days < fastest.days) {
      fastest = { company: app.company_name || 'Unknown', days }
    }
  }
  return fastest.days < Infinity ? fastest : null
}

export function computeSlowestHiringProcess(applications: Application[]): { company: string; days: number } | null {
  const hired = applications.filter(a => a.status === 'accepted')
  if (hired.length === 0) return null
  let slowest = { company: '', days: -1 }
  for (const app of hired) {
    const days = Math.round((new Date(app.updated_at).getTime() - new Date(app.created_at).getTime()) / 86400000)
    if (days > slowest.days) {
      slowest = { company: app.company_name || 'Unknown', days }
    }
  }
  return slowest.days > 0 ? slowest : null
}

export function computeMedianHiringDuration(applications: Application[]): number {
  const hired = applications.filter(a => a.status === 'accepted')
  if (hired.length === 0) return 0
  const durations = hired
    .map(a => Math.round((new Date(a.updated_at).getTime() - new Date(a.created_at).getTime()) / 86400000))
    .filter(d => d > 0)
    .sort((a, b) => a - b)
  if (durations.length === 0) return 0
  const mid = Math.floor(durations.length / 2)
  return durations.length % 2 === 0
    ? Math.round((durations[mid - 1] + durations[mid]) / 2)
    : durations[mid]
}

export function computeCohortAnalytics(applications: Application[], period: 'weekly' | 'monthly' | 'quarterly'): CohortPeriod[] {
  const groups = new Map<string, Application[]>()

  for (const app of applications) {
    const date = new Date(app.created_at)
    let key: string
    if (period === 'weekly') {
      const weekStart = new Date(date)
      weekStart.setDate(weekStart.getDate() - weekStart.getDay())
      key = weekStart.toISOString().split('T')[0]
    } else if (period === 'monthly') {
      key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
    } else {
      const q = Math.floor(date.getMonth() / 3) + 1
      key = `${date.getFullYear()}-Q${q}`
    }
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)!.push(app)
  }

  const sorted = Array.from(groups.entries()).sort(([a], [b]) => a.localeCompare(b))

  return sorted.map(([key, apps]) => {
    const interviews = apps.filter(a =>
      ['technical_interview', 'hr_interview', 'final_interview'].includes(a.status)
    ).length
    const offers = apps.filter(a =>
      ['offer', 'negotiation', 'accepted'].includes(a.status)
    ).length
    const acceptances = apps.filter(a => a.status === 'accepted').length

    return {
      label: key,
      applications: apps.length,
      interviews,
      offers,
      acceptances,
      interviewRate: apps.length > 0 ? Math.round((interviews / apps.length) * 100) : 0,
      offerRate: apps.length > 0 ? Math.round((offers / apps.length) * 100) : 0,
      acceptanceRate: apps.length > 0 ? Math.round((acceptances / apps.length) * 100) : 0,
    }
  })
}

export function computeHeatMap(applications: Application[]): HeatMapData {
  const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
  const hours = Array.from({ length: 12 }, (_, i) => `${String(i * 2).padStart(2, '0')}:00`)

  const data: number[][] = weekdays.map(() => hours.map(() => 0))
  let maxValue = 0

  for (const app of applications) {
    const d = new Date(app.created_at)
    const day = d.getDay()
    const hour = Math.floor(d.getHours() / 2)
    if (hour < hours.length) {
      data[day][hour]++
      if (data[day][hour] > maxValue) maxValue = data[day][hour]
    }
  }

  return { weekday: weekdays, hourSlots: hours, data, maxValue }
}
