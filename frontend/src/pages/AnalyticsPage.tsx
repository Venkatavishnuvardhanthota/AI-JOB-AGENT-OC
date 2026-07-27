import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { analyticsService } from '@/services/analytics'
import { AnalyticsOverviewCards } from '@/components/analytics/analytics-overview-cards'
import { PipelineFunnel } from '@/components/analytics/pipeline-funnel'
import { BottleneckDetection } from '@/components/analytics/bottleneck-detection'
import { ResumePerformance } from '@/components/analytics/resume-performance'
import { CompanyIntelligence } from '@/components/analytics/company-intelligence'
import { SourceAnalytics } from '@/components/analytics/source-analytics'
import { SalaryAnalytics } from '@/components/analytics/salary-analytics'
import { TimelineAnalytics } from '@/components/analytics/timeline-analytics'
import { GoalsProgress } from '@/components/analytics/goals-progress'
import { InsightCards } from '@/components/analytics/insight-cards'
import { AnalyticsExport } from '@/components/analytics/analytics-export'
import { AnalyticsFilters, type AnalyticsDateRange } from '@/components/analytics/analytics-filters'
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts'

type AnalyticsSection = 'overview' | 'pipeline' | 'resume' | 'companies' | 'sources' | 'salary' | 'timeline' | 'goals'

const SECTIONS: { key: AnalyticsSection; label: string }[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'pipeline', label: 'Pipeline' },
  { key: 'resume', label: 'Resume' },
  { key: 'companies', label: 'Companies' },
  { key: 'sources', label: 'Sources' },
  { key: 'salary', label: 'Salary' },
  { key: 'timeline', label: 'Timeline' },
  { key: 'goals', label: 'Goals' },
]

export function AnalyticsPage() {
  const [activeSection, setActiveSection] = useState<AnalyticsSection>('overview')
  const [dateRange, setDateRange] = useState<AnalyticsDateRange>({ from: '', to: '' })

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['analytics', 'stats'],
    queryFn: () => analyticsService.getStats(),
  })

  const { data: allApps, isLoading: appsLoading } = useQuery({
    queryKey: ['analytics', 'applications', dateRange],
    queryFn: () => analyticsService.getAllApplications(),
  })

  const applications = allApps || []

  const filteredApps = useMemo(() => {
    if (!dateRange.from && !dateRange.to) return applications
    return applications.filter(a => {
      const created = new Date(a.created_at).getTime()
      if (dateRange.from && created < new Date(dateRange.from).getTime()) return false
      if (dateRange.to && created > new Date(dateRange.to + 'T23:59:59').getTime()) return false
      return true
    })
  }, [applications, dateRange])

  const funnel = useMemo(() => filteredApps.length > 0 ? analyticsService.computeFunnel(filteredApps) : null, [filteredApps])
  const bottlenecks = useMemo(() => filteredApps.length > 0 ? analyticsService.detectBottlenecks(filteredApps) : [], [filteredApps])
  const resumePerf = useMemo(() => analyticsService.computeResumePerformance(filteredApps), [filteredApps])
  const clPerf = useMemo(() => analyticsService.computeCoverLetterPerformance(filteredApps), [filteredApps])
  const companies = useMemo(() => analyticsService.computeCompanyIntelligence(filteredApps), [filteredApps])
  const sources = useMemo(() => analyticsService.computeSourceAnalytics(filteredApps), [filteredApps])
  const salaryData = useMemo(() => analyticsService.computeSalaryAnalytics(filteredApps), [filteredApps])
  const timelineData = useMemo(() => analyticsService.computeTimelineAnalytics(filteredApps), [filteredApps])

  const goalsState = useMemo(() => {
    const saved = analyticsService.goalService.list()
    return analyticsService.goalService.updateProgress(saved, filteredApps)
  }, [filteredApps])

  const insights = useMemo(() => filteredApps.length > 0 && funnel ? analyticsService.generateInsights(filteredApps, resumePerf, funnel) : [], [filteredApps, resumePerf, funnel])

  useKeyboardShortcuts([
    { key: 'Escape', handler: () => setActiveSection('overview'), ignoreWhenFocused: false },
  ])

  const loading = statsLoading || appsLoading

  if (loading && !applications.length) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="h-8 w-48 bg-dark-700 rounded animate-pulse" />
            <div className="h-4 w-72 bg-dark-700 rounded animate-pulse" />
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="h-24 bg-dark-800 rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Analytics</h1>
          <p className="text-sm text-muted-foreground">
            Job Search Intelligence Center
            {filteredApps.length > 0 && ` — ${filteredApps.length} applications analyzed`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <AnalyticsFilters dateRange={dateRange} onDateRangeChange={setDateRange} />
          <AnalyticsExport applications={filteredApps} />
        </div>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-2">
        {SECTIONS.map(s => (
          <button
            key={s.key}
            onClick={() => setActiveSection(s.key)}
            className={`px-3 py-1.5 text-sm rounded-lg whitespace-nowrap transition-colors ${
              activeSection === s.key
                ? 'bg-primary/10 text-primary border border-primary/30'
                : 'bg-dark-800 text-muted-foreground border border-glass-border hover:text-foreground'
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {activeSection === 'overview' && (
        <div className="space-y-6">
          <AnalyticsOverviewCards stats={stats} loading={statsLoading} />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <InsightCards insights={insights} loading={loading} />
            <GoalsProgress goals={goalsState} onUpdate={(g) => analyticsService.goalService.update(g)} loading={loading} />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <PipelineFunnel funnel={funnel} loading={loading} />
            <BottleneckDetection bottlenecks={bottlenecks} loading={loading} />
          </div>
        </div>
      )}

      {activeSection === 'pipeline' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PipelineFunnel funnel={funnel} loading={loading} />
          <BottleneckDetection bottlenecks={bottlenecks} loading={loading} />
        </div>
      )}

      {activeSection === 'resume' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ResumePerformance title="Resume Performance" data={resumePerf} loading={loading} />
          <ResumePerformance title="Cover Letter Performance" data={clPerf} loading={loading} />
        </div>
      )}

      {activeSection === 'companies' && (
        <CompanyIntelligence data={companies} loading={loading} />
      )}

      {activeSection === 'sources' && (
        <SourceAnalytics data={sources} loading={loading} />
      )}

      {activeSection === 'salary' && (
        <SalaryAnalytics data={salaryData} loading={loading} />
      )}

      {activeSection === 'timeline' && (
        <TimelineAnalytics data={timelineData} loading={loading} />
      )}

      {activeSection === 'goals' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <GoalsProgress goals={goalsState} onUpdate={(g) => analyticsService.goalService.update(g)} loading={loading} />
          <InsightCards insights={insights} loading={loading} />
        </div>
      )}
    </div>
  )
}
