import { useState, useMemo, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { applicationService } from '@/services/application'
import { calendarService } from '@/services/calendar'
import { CareerCalendar } from '@/components/calendar/career-calendar'
import { CalendarDashboard } from '@/components/calendar/calendar-dashboard'
import { InterviewScheduler } from '@/components/calendar/interview-scheduler'
import { FollowUpPlanner } from '@/components/calendar/follow-up-planner'
import { ReminderCenter } from '@/components/calendar/reminder-center'
import { CareerTimeline } from '@/components/calendar/career-timeline'
import { TimelineIntelligence } from '@/components/calendar/timeline-intelligence'
import { CohortAnalytics } from '@/components/calendar/cohort-analytics'
import { HeatMap } from '@/components/calendar/heat-map'
import { BenchmarkCards } from '@/components/calendar/benchmark-cards'
import { CalendarExport } from '@/components/calendar/calendar-export'
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts'

type CalendarTab = 'dashboard' | 'calendar' | 'timeline' | 'intelligence' | 'cohort' | 'heatmap' | 'benchmarks' | 'followups' | 'reminders'

const TABS: { key: CalendarTab; label: string }[] = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'calendar', label: 'Calendar' },
  { key: 'timeline', label: 'Timeline' },
  { key: 'intelligence', label: 'Intelligence' },
  { key: 'cohort', label: 'Cohorts' },
  { key: 'heatmap', label: 'Heat Map' },
  { key: 'benchmarks', label: 'Benchmarks' },
  { key: 'followups', label: 'Follow-ups' },
  { key: 'reminders', label: 'Reminders' },
]

export function CalendarPage() {
  const [activeTab, setActiveTab] = useState<CalendarTab>('dashboard')
  const [showInterviewForm, setShowInterviewForm] = useState(false)
  const [interviewDate, setInterviewDate] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)

  const { data: allApps, isLoading } = useQuery({
    queryKey: ['applications', 'all', refreshKey],
    queryFn: () => {
      return applicationService.list({ page_size: 500 } as any).then(r => r.items)
    },
  })

  const applications = allApps || []

  const events = useMemo(() => {
    const synced = calendarService.syncFromApplications(applications)
    return synced
  }, [applications, refreshKey])

  const followUps = useMemo(() => {
    const generated = calendarService.generateFollowUpsFromApplications(applications)
    return generated
  }, [applications, refreshKey])

  const reminders = useMemo(() => {
    const generated = calendarService.generateRemindersFromApplications(applications)
    return generated
  }, [applications, refreshKey])

  useKeyboardShortcuts([
    { key: 'Escape', handler: () => { setShowInterviewForm(false) }, ignoreWhenFocused: false },
  ])

  const handleRefresh = useCallback(() => {
    setRefreshKey(k => k + 1)
  }, [])

  const handleScheduleInterview = useCallback((date: string) => {
    setInterviewDate(date)
    setShowInterviewForm(true)
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Career Calendar</h1>
          <p className="text-sm text-muted-foreground">
            {events.length} events · {followUps.filter(f => f.status === 'pending').length} pending follow-ups · {reminders.filter(r => r.category !== 'completed' && r.category !== 'dismissed').length} active reminders
          </p>
        </div>
        <div className="flex items-center gap-2">
          <CalendarExport events={events} followUps={followUps} />
        </div>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-2">
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-3 py-1.5 text-sm rounded-lg whitespace-nowrap transition-colors ${
              activeTab === tab.key
                ? 'bg-primary/10 text-primary border border-primary/30'
                : 'bg-dark-800 text-muted-foreground border border-glass-border hover:text-foreground'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'dashboard' && (
        <CalendarDashboard
          events={events}
          followUps={followUps}
          onViewCalendar={() => setActiveTab('calendar')}
          onViewFollowUps={() => setActiveTab('followups')}
        />
      )}

      {activeTab === 'calendar' && (
        <div className="space-y-6">
          <CareerCalendar events={events} onScheduleInterview={handleScheduleInterview} />
          {showInterviewForm && (
            <InterviewScheduler
              defaultDate={interviewDate}
              onClose={() => setShowInterviewForm(false)}
              onScheduled={handleRefresh}
            />
          )}
        </div>
      )}

      {activeTab === 'timeline' && (
        <CareerTimeline
          applications={applications}
          events={events}
          followUps={followUps}
          reminders={reminders}
        />
      )}

      {activeTab === 'intelligence' && (
        <TimelineIntelligence applications={applications} loading={isLoading} />
      )}

      {activeTab === 'cohort' && (
        <CohortAnalytics applications={applications} loading={isLoading} />
      )}

      {activeTab === 'heatmap' && (
        <HeatMap applications={applications} loading={isLoading} />
      )}

      {activeTab === 'benchmarks' && (
        <BenchmarkCards applications={applications} loading={isLoading} />
      )}

      {activeTab === 'followups' && (
        <FollowUpPlanner tasks={followUps} onUpdate={handleRefresh} />
      )}

      {activeTab === 'reminders' && (
        <ReminderCenter onUpdate={handleRefresh} />
      )}
    </div>
  )
}
