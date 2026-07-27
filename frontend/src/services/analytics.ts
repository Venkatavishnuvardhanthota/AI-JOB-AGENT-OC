import { applicationService } from './application'
import { APPLICATION_STATUSES, getStatusLabel, getStatusCategory } from './status'
import type { Application, ApplicationStatus, ApplicationStats } from '@/types'

export interface FunnelStage {
  status: ApplicationStatus
  label: string
  count: number
  category: string
}

export interface FunnelMetrics {
  stages: FunnelStage[]
  totalInPipeline: number
  conversionRates: { from: string; to: string; rate: number }[]
  dropOffRates: { from: string; to: string; rate: number }[]
  averageDaysBetweenStages: { from: string; to: string; days: number }[]
  bottlenecks: Bottleneck[]
}

export interface Bottleneck {
  stage: string
  type: 'queue' | 'stale' | 'waiting' | 'no_update'
  severity: 'info' | 'warning' | 'critical'
  message: string
  suggestion: string
  count: number
}

export interface ResumePerformance {
  resumeId: string
  version: string
  applications: number
  interviews: number
  assessments: number
  offers: number
  acceptances: number
  responseRate: number
  interviewRate: number
  offerRate: number
  averageResponseDays: number
  averageHiringDays: number
}

export interface CompanyIntelligence {
  company: string
  applications: number
  responses: number
  interviews: number
  offers: number
  acceptances: number
  responseRate: number
  interviewRate: number
  offerRate: number
  averageResponseDays: number
  averageHiringDays: number
  recruiters: string[]
  locations: string[]
  sources: string[]
}

export interface SourceAnalytics {
  source: string
  applications: number
  responses: number
  interviews: number
  offers: number
  acceptances: number
  responseRate: number
  interviewRate: number
  offerRate: number
  averageResponseDays: number
}

export interface SalaryAnalytics {
  expected: { min: number; max: number; avg: number }
  offered: { min: number; max: number; avg: number }
  accepted: { min: number; max: number; avg: number }
  byRole: { role: string; avg: number; count: number }[]
  byLocation: { location: string; avg: number; count: number }[]
}

export interface TimelineAnalytics {
  applicationsPerWeek: { week: string; count: number }[]
  interviewsPerMonth: { month: string; count: number }[]
  offersOverTime: { month: string; count: number }[]
  dailyActivity: { date: string; count: number }[]
  weeklyActivity: { week: string; count: number }[]
  monthlyActivity: { month: string; count: number }[]
}

export interface Goal {
  id: string
  type: 'applications' | 'interviews' | 'offers' | 'acceptances'
  target: number
  current: number
  label: string
  createdAt: string
}

export interface Insight {
  id: string
  type: 'positive' | 'negative' | 'info'
  title: string
  description: string
  metric?: string
  change?: number
}

const PREFIX = 'ajapp_analytics_'

function getGoals(): Goal[] {
  try {
    const raw = localStorage.getItem(PREFIX + 'goals')
    return raw ? JSON.parse(raw) : DEFAULT_GOALS
  } catch { return DEFAULT_GOALS }
}

function setGoals(goals: Goal[]): void {
  try { localStorage.setItem(PREFIX + 'goals', JSON.stringify(goals)) } catch {}
}

const DEFAULT_GOALS: Goal[] = [
  { id: 'goal_apps', type: 'applications', target: 100, current: 0, label: 'Applications', createdAt: new Date().toISOString() },
  { id: 'goal_interviews', type: 'interviews', target: 20, current: 0, label: 'Interviews', createdAt: new Date().toISOString() },
  { id: 'goal_offers', type: 'offers', target: 5, current: 0, label: 'Offers', createdAt: new Date().toISOString() },
  { id: 'goal_acceptances', type: 'acceptances', target: 1, current: 0, label: 'Acceptances', createdAt: new Date().toISOString() },
]

function countByStatus(applications: Application[], statuses: ApplicationStatus[]): number {
  return applications.filter(a => statuses.includes(a.status)).length
}

function parseSalary(salary: string): number | null {
  const cleaned = salary.replace(/[^0-9kK\-]/g, '')
  if (!cleaned) return null
  const parts = cleaned.split('-')
  const avg = parts.reduce((sum, p) => {
    const num = p.toLowerCase().includes('k') ? parseFloat(p) * 1000 : parseFloat(p)
    return sum + (isNaN(num) ? 0 : num)
  }, 0) / parts.length
  return avg || null
}

export const analyticsService = {
  async getStats(): Promise<ApplicationStats> {
    return applicationService.getStats()
  },

  async getAllApplications(): Promise<Application[]> {
    const all: Application[] = []
    let page = 1
    let hasMore = true
    while (hasMore) {
      const res = await applicationService.list({ page, page_size: 200 } as any)
      all.push(...res.items)
      hasMore = res.items.length === 200
      page++
    }
    return all
  },

  computeFunnel(applications: Application[]): FunnelMetrics {
    const stages: FunnelStage[] = APPLICATION_STATUSES.map(s => ({
      status: s,
      label: getStatusLabel(s),
      count: applications.filter(a => a.status === s).length,
      category: getStatusCategory(s),
    }))

    const totalInPipeline = applications.length

    const conversionRates: { from: string; to: string; rate: number }[] = []
    const dropOffRates: { from: string; to: string; rate: number }[] = []
    for (let i = 0; i < stages.length - 1; i++) {
      const from = stages[i]
      const to = stages[i + 1]
      if (from.count > 0) {
        const rate = Math.round((to.count / from.count) * 100)
        conversionRates.push({ from: from.label, to: to.label, rate })
        dropOffRates.push({ from: from.label, to: to.label, rate: 100 - rate })
      }
    }

    const bottlenecks: Bottleneck[] = this.detectBottlenecks(applications, stages)

    return { stages, totalInPipeline, conversionRates, dropOffRates, averageDaysBetweenStages: [], bottlenecks }
  },

  detectBottlenecks(applications: Application[], _stages?: FunnelStage[]): Bottleneck[] {
    const bottlenecks: Bottleneck[] = []

    const appliedApps = applications.filter(a => a.status === 'applied')
    if (appliedApps.length > 25) {
      bottlenecks.push({
        stage: 'Applied', type: 'queue', severity: 'warning',
        message: `Large applied queue: ${appliedApps.length} applications`,
        suggestion: 'Follow up on older applications or withdraw stale ones.',
        count: appliedApps.length,
      })
    }

    const interviewApps = applications.filter(a =>
      ['technical_interview', 'hr_interview', 'final_interview'].includes(a.status)
    )
    const staleInterviews = interviewApps.filter(a => {
      const days = Math.floor((Date.now() - new Date(a.updated_at).getTime()) / 86400000)
      return days > 14
    })
    if (staleInterviews.length > 0) {
      bottlenecks.push({
        stage: 'Interview', type: 'stale', severity: 'warning',
        message: `${staleInterviews.length} interview${staleInterviews.length > 1 ? 's' : ''} waiting over 14 days`,
        suggestion: 'Send a follow-up to check on interview status.',
        count: staleInterviews.length,
      })
    }

    const offerApps = applications.filter(a => a.status === 'offer' || a.status === 'negotiation')
    const expiredOffers = offerApps.filter(a => a.deadline && new Date(a.deadline) < new Date())
    if (expiredOffers.length > 0) {
      bottlenecks.push({
        stage: 'Offer', type: 'waiting', severity: 'critical',
        message: `${expiredOffers.length} expired offer${expiredOffers.length > 1 ? 's' : ''}`,
        suggestion: 'Contact the recruiter immediately about expired offers.',
        count: expiredOffers.length,
      })
    }

    const noUpdateApps = applications.filter(a => {
      const days = Math.floor((Date.now() - new Date(a.updated_at).getTime()) / 86400000)
      return days > 30 && !['accepted', 'rejected', 'withdrawn', 'archived'].includes(a.status)
    })
    if (noUpdateApps.length >= 5) {
      bottlenecks.push({
        stage: 'Pipeline', type: 'no_update', severity: 'info',
        message: `${noUpdateApps.length} applications with no updates in 30+ days`,
        suggestion: 'Review and clean up stale applications.',
        count: noUpdateApps.length,
      })
    }

    return bottlenecks
  },

  computeResumePerformance(applications: Application[]): ResumePerformance[] {
    const byResume = new Map<string, Application[]>()
    for (const app of applications) {
      if (!app.resume_id) continue
      if (!byResume.has(app.resume_id)) byResume.set(app.resume_id, [])
      byResume.get(app.resume_id)!.push(app)
    }

    return Array.from(byResume.entries()).map(([resumeId, apps]) => {
      const interviews = countByStatus(apps, ['technical_interview', 'hr_interview', 'final_interview'])
      const assessments = countByStatus(apps, ['assessment'])
      const offers = countByStatus(apps, ['offer', 'negotiation'])
      const acceptances = countByStatus(apps, ['accepted'])
      const responses = apps.filter(a => a.status !== 'saved' && a.status !== 'preparing' && a.status !== 'ready_to_apply').length

      return {
        resumeId,
        version: `Resume ${resumeId.slice(0, 8)}`,
        applications: apps.length,
        interviews,
        assessments,
        offers,
        acceptances,
        responseRate: apps.length > 0 ? Math.round((responses / apps.length) * 100) : 0,
        interviewRate: apps.length > 0 ? Math.round((interviews / apps.length) * 100) : 0,
        offerRate: apps.length > 0 ? Math.round((offers / apps.length) * 100) : 0,
        averageResponseDays: 0,
        averageHiringDays: 0,
      }
    }).sort((a, b) => b.offerRate - a.offerRate)
  },

  computeCoverLetterPerformance(applications: Application[]): ResumePerformance[] {
    const byCL = new Map<string, Application[]>()
    for (const app of applications) {
      if (!app.cover_letter_id) continue
      if (!byCL.has(app.cover_letter_id)) byCL.set(app.cover_letter_id, [])
      byCL.get(app.cover_letter_id)!.push(app)
    }

    return Array.from(byCL.entries()).map(([clId, apps]) => {
      const interviews = countByStatus(apps, ['technical_interview', 'hr_interview', 'final_interview'])
      const offers = countByStatus(apps, ['offer', 'negotiation'])
      const acceptances = countByStatus(apps, ['accepted'])
      const responses = apps.filter(a => a.status !== 'saved').length

      return {
        resumeId: clId,
        version: `Cover Letter ${clId.slice(0, 8)}`,
        applications: apps.length,
        interviews,
        assessments: 0,
        offers,
        acceptances,
        responseRate: apps.length > 0 ? Math.round((responses / apps.length) * 100) : 0,
        interviewRate: apps.length > 0 ? Math.round((interviews / apps.length) * 100) : 0,
        offerRate: apps.length > 0 ? Math.round((offers / apps.length) * 100) : 0,
        averageResponseDays: 0,
        averageHiringDays: 0,
      }
    }).sort((a, b) => b.offerRate - a.offerRate)
  },

  computeCompanyIntelligence(applications: Application[]): CompanyIntelligence[] {
    const byCompany = new Map<string, Application[]>()
    for (const app of applications) {
      const name = app.company_name || 'Unknown'
      if (!byCompany.has(name)) byCompany.set(name, [])
      byCompany.get(name)!.push(app)
    }

    return Array.from(byCompany.entries()).map(([company, apps]) => {
      const interviews = countByStatus(apps, ['technical_interview', 'hr_interview', 'final_interview'])
      const offers = countByStatus(apps, ['offer', 'negotiation'])
      const acceptances = countByStatus(apps, ['accepted'])
      const responses = apps.filter(a => a.status !== 'saved' && a.status !== 'preparing').length
      const recruiters = [...new Set(apps.map(a => a.recruiter).filter((r): r is string => !!r))]
      const locations = [...new Set(apps.map(a => a.location).filter((l): l is string => !!l))]
      const sources = [...new Set(apps.map(a => a.source).filter((s): s is string => !!s))]

      return {
        company,
        applications: apps.length,
        responses,
        interviews,
        offers,
        acceptances,
        responseRate: apps.length > 0 ? Math.round((responses / apps.length) * 100) : 0,
        interviewRate: apps.length > 0 ? Math.round((interviews / apps.length) * 100) : 0,
        offerRate: apps.length > 0 ? Math.round((offers / apps.length) * 100) : 0,
        averageResponseDays: 0,
        averageHiringDays: 0,
        recruiters,
        locations,
        sources,
      }
    }).sort((a, b) => b.interviewRate - a.interviewRate)
  },

  computeSourceAnalytics(applications: Application[]): SourceAnalytics[] {
    const bySource = new Map<string, Application[]>()
    for (const app of applications) {
      const source = app.source || 'Direct'
      if (!bySource.has(source)) bySource.set(source, [])
      bySource.get(source)!.push(app)
    }

    return Array.from(bySource.entries()).map(([source, apps]) => {
      const interviews = countByStatus(apps, ['technical_interview', 'hr_interview', 'final_interview'])
      const offers = countByStatus(apps, ['offer', 'negotiation'])
      const acceptances = countByStatus(apps, ['accepted'])
      const responses = apps.filter(a => a.status !== 'saved' && a.status !== 'preparing').length

      return {
        source,
        applications: apps.length,
        responses,
        interviews,
        offers,
        acceptances,
        responseRate: apps.length > 0 ? Math.round((responses / apps.length) * 100) : 0,
        interviewRate: apps.length > 0 ? Math.round((interviews / apps.length) * 100) : 0,
        offerRate: apps.length > 0 ? Math.round((offers / apps.length) * 100) : 0,
        averageResponseDays: 0,
      }
    }).sort((a, b) => b.applications - a.applications)
  },

  computeSalaryAnalytics(applications: Application[]): SalaryAnalytics {
    const salaries = applications.map(a => ({ salary: a.salary, status: a.status })).filter(s => s.salary)
    const parsed = salaries.map(s => ({ ...s, parsed: parseSalary(s.salary!) })).filter(s => s.parsed !== null) as { salary: string; status: ApplicationStatus; parsed: number }[]

    const expected = parsed.filter(s => s.status === 'saved' || s.status === 'preparing' || s.status === 'ready_to_apply')
    const offered = parsed.filter(s => s.status === 'offer' || s.status === 'negotiation')
    const accepted = parsed.filter(s => s.status === 'accepted')

    const avg = (arr: number[]) => arr.length > 0 ? Math.round(arr.reduce((a, b) => a + b, 0) / arr.length) : 0
    const min = (arr: number[]) => arr.length > 0 ? Math.min(...arr) : 0
    const max = (arr: number[]) => arr.length > 0 ? Math.max(...arr) : 0

    const byRole = new Map<string, number[]>()
    for (const s of parsed) {
      const role = 'All Roles'
      if (!byRole.has(role)) byRole.set(role, [])
      byRole.get(role)!.push(s.parsed)
    }

    const byLocation = new Map<string, number[]>()
    for (const app of applications) {
      if (app.salary && app.location) {
        const parsedS = parseSalary(app.salary)
        if (parsedS) {
          if (!byLocation.has(app.location)) byLocation.set(app.location, [])
          byLocation.get(app.location)!.push(parsedS)
        }
      }
    }

    return {
      expected: { min: min(expected.map(s => s.parsed)), max: max(expected.map(s => s.parsed)), avg: avg(expected.map(s => s.parsed)) },
      offered: { min: min(offered.map(s => s.parsed)), max: max(offered.map(s => s.parsed)), avg: avg(offered.map(s => s.parsed)) },
      accepted: { min: min(accepted.map(s => s.parsed)), max: max(accepted.map(s => s.parsed)), avg: avg(accepted.map(s => s.parsed)) },
      byRole: Array.from(byRole.entries()).map(([role, vals]) => ({ role, avg: avg(vals), count: vals.length })),
      byLocation: Array.from(byLocation.entries()).map(([loc, vals]) => ({ location: loc, avg: avg(vals), count: vals.length })),
    }
  },

  computeTimelineAnalytics(applications: Application[]): TimelineAnalytics {
    const weekMap = new Map<string, number>()
    const monthMap = new Map<string, number>()
    const dayMap = new Map<string, number>()

    for (const app of applications) {
      const date = new Date(app.created_at)
      const week = `${date.getFullYear()}-W${String(Math.ceil((date.getDate()) / 7)).padStart(2, '0')}`
      const month = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
      const day = date.toISOString().split('T')[0]

      weekMap.set(week, (weekMap.get(week) || 0) + 1)
      monthMap.set(month, (monthMap.get(month) || 0) + 1)
      dayMap.set(day, (dayMap.get(day) || 0) + 1)
    }

    const sortedWeeks = Array.from(weekMap.entries()).sort(([a], [b]) => a.localeCompare(b))
    const sortedMonths = Array.from(monthMap.entries()).sort(([a], [b]) => a.localeCompare(b))
    const sortedDays = Array.from(dayMap.entries()).sort(([a], [b]) => a.localeCompare(b))

    return {
      applicationsPerWeek: sortedWeeks.map(([week, count]) => ({ week, count })),
      interviewsPerMonth: sortedMonths.map(([month, count]) => ({ month, count })),
      offersOverTime: sortedMonths.map(([month, count]) => ({ month, count })),
      dailyActivity: sortedDays.map(([date, count]) => ({ date, count })),
      weeklyActivity: sortedWeeks.map(([week, count]) => ({ week, count })),
      monthlyActivity: sortedMonths.map(([month, count]) => ({ month, count })),
    }
  },

  generateInsights(applications: Application[], resumePerf: ResumePerformance[], _funnel: FunnelMetrics): Insight[] {
    const insights: Insight[] = []

    const interviewRate = applications.length > 0
      ? Math.round((countByStatus(applications, ['technical_interview', 'hr_interview', 'final_interview']) / applications.length) * 100)
      : 0
    if (interviewRate > 30) {
      insights.push({ id: 'insight_int_rate', type: 'positive', title: 'Strong Interview Rate', description: `Your interview rate of ${interviewRate}% is above average. Keep up the good work!`, metric: `${interviewRate}%` })
    } else if (interviewRate > 0) {
      insights.push({ id: 'insight_int_rate_low', type: 'info', title: 'Room for Improvement', description: `Your interview rate is ${interviewRate}%. Consider optimizing your resume and cover letter.`, metric: `${interviewRate}%` })
    }

    if (resumePerf.length >= 2) {
      const best = resumePerf[0]
      const worst = resumePerf[resumePerf.length - 1]
      if (best.offerRate > worst.offerRate) {
        const diff = best.offerRate - worst.offerRate
        insights.push({
          id: 'insight_resume', type: 'positive', title: 'Resume Performance Gap',
          description: `${best.version} performs ${diff}% better than ${worst.version} in offer rate.`,
          metric: `${diff}% better`,
        })
      }
    }

    const referralApps = applications.filter(a => a.referral)
    const nonReferralApps = applications.filter(a => !a.referral)
    if (referralApps.length >= 3 && nonReferralApps.length >= 3) {
      const refIntRate = Math.round((countByStatus(referralApps, ['technical_interview', 'hr_interview', 'final_interview']) / referralApps.length) * 100)
      const nonRefIntRate = Math.round((countByStatus(nonReferralApps, ['technical_interview', 'hr_interview', 'final_interview']) / nonReferralApps.length) * 100)
      if (refIntRate > nonRefIntRate) {
        insights.push({
          id: 'insight_referral', type: 'positive', title: 'Referrals Work',
          description: `Referrals generate ${refIntRate}% interview rate vs ${nonRefIntRate}% without.`,
          metric: `${refIntRate - nonRefIntRate}% higher`,
        })
      }
    }

    const bottlenecks = this.detectBottlenecks(applications)
    for (const b of bottlenecks) {
      insights.push({
        id: `insight_bottleneck_${b.type}`, type: 'negative', title: `Bottleneck: ${b.stage}`,
        description: b.message, metric: `${b.count} items`,
      })
    }

    const remoteApps = applications.filter(a => a.work_type?.toLowerCase() === 'remote')
    const onsiteApps = applications.filter(a => a.work_type?.toLowerCase() === 'onsite' || a.work_type?.toLowerCase() === 'in-office')
    if (remoteApps.length >= 5 && onsiteApps.length >= 5) {
      const remoteIntRate = Math.round((countByStatus(remoteApps, ['technical_interview', 'hr_interview', 'final_interview']) / remoteApps.length) * 100)
      const onsiteIntRate = Math.round((countByStatus(onsiteApps, ['technical_interview', 'hr_interview', 'final_interview']) / onsiteApps.length) * 100)
      if (remoteIntRate > onsiteIntRate) {
        insights.push({
          id: 'insight_remote', type: 'positive', title: 'Remote Advantage',
          description: `Remote jobs have ${remoteIntRate}% interview rate vs ${onsiteIntRate}% on-site.`,
          metric: `${remoteIntRate - onsiteIntRate}% higher`,
        })
      }
    }

    const appliedCount = countByStatus(applications, ['applied', 'application_viewed'])
    if (appliedCount > 10) {
      const bottleneck = applications.filter(a => a.status === 'applied').length
      const viewed = countByStatus(applications, ['application_viewed'])
      if (bottleneck > viewed * 2) {
        insights.push({
          id: 'insight_applied_queue', type: 'negative', title: 'Applied Queue Growing',
          description: `${bottleneck} applications pending review. Only ${viewed} have been viewed by recruiters.`,
          metric: `${bottleneck} pending`,
        })
      }
    }

    const sourceData = this.computeSourceAnalytics(applications)
    if (sourceData.length >= 2) {
      const bestSource = sourceData.sort((a, b) => b.interviewRate - a.interviewRate)[0]
      const mostApps = sourceData.sort((a, b) => b.applications - a.applications)[0]
      if (bestSource.source !== mostApps.source) {
        insights.push({
          id: 'insight_source', type: 'info', title: 'Source Effectiveness',
          description: `${bestSource.source} has the highest interview rate (${bestSource.interviewRate}%), but you apply most through ${mostApps.source}.`,
          metric: `${bestSource.source}: ${bestSource.interviewRate}%`,
        })
      }
    }

    return insights
  },

  goalService: {
    list(): Goal[] {
      return getGoals()
    },

    update(goals: Goal[]): void {
      setGoals(goals)
    },

    updateProgress(goals: Goal[], applications: Application[]): Goal[] {
      const totalApps = applications.length
      const interviews = countByStatus(applications, ['technical_interview', 'hr_interview', 'final_interview'])
      const offers = countByStatus(applications, ['offer', 'negotiation'])
      const acceptances = countByStatus(applications, ['accepted'])

      return goals.map(g => {
        switch (g.type) {
          case 'applications': return { ...g, current: totalApps }
          case 'interviews': return { ...g, current: interviews }
          case 'offers': return { ...g, current: offers }
          case 'acceptances': return { ...g, current: acceptances }
          default: return g
        }
      })
    },
  },

  exportToCSV(applications: Application[]): string {
    const headers = ['Job Title', 'Company', 'Status', 'Priority', 'Location', 'Salary', 'Source', 'Recruiter', 'Applied Date', 'Deadline', 'Created', 'Updated']
    const rows = applications.map(a => [
      a.job_title, a.company_name, a.status, a.priority, a.location || '',
      a.salary || '', a.source || '', a.recruiter || '',
      a.applied_date || '', a.deadline || '', a.created_at, a.updated_at,
    ].map(v => `"${String(v).replace(/"/g, '""')}"`).join(','))

    return [headers.join(','), ...rows].join('\n')
  },
}
