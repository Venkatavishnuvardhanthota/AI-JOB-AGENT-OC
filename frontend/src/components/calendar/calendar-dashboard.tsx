import { useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

import { cn } from '@/lib/utils'
import type { CalendarEvent, FollowUpTask } from '@/services/calendar'
import { Calendar, Clock, Target, AlertTriangle, CheckCircle2, ArrowRight } from 'lucide-react'

interface CalendarDashboardProps {
  events: CalendarEvent[]
  followUps: FollowUpTask[]
  onViewCalendar: () => void
  onViewFollowUps: () => void
}

export function CalendarDashboard({ events, followUps, onViewCalendar, onViewFollowUps }: CalendarDashboardProps) {
  const today = new Date()
  const todayStr = today.toISOString().split('T')[0]

  const todayEvents = useMemo(() =>
    events.filter(e => new Date(e.date).toISOString().split('T')[0] === todayStr),
  [events, todayStr])

  const pendingFollowUps = useMemo(() =>
    followUps.filter(f => f.status === 'pending'),
  [followUps])

  const upcomingInterviews = useMemo(() =>
    events.filter(e => e.type === 'interview' && e.status === 'scheduled').slice(0, 5),
  [events])

  const deadlines = useMemo(() => {
    const now = new Date()
    const weekEnd = new Date(now.getTime() + 7 * 86400000)
    return events.filter(e => {
      if (e.type !== 'deadline' && e.type !== 'offer_expiry') return false
      const d = new Date(e.date)
      return d >= now && d <= weekEnd
    }).slice(0, 5)
  }, [events])

  const weeklyCount = useMemo(() => {
    const weekStart = new Date(today.getTime() - today.getDay() * 86400000)
    const weekEnd = new Date(weekStart.getTime() + 7 * 86400000)
    const weekEvents = events.filter(e => {
      const d = new Date(e.date)
      return d >= weekStart && d < weekEnd
    })
    return {
      total: weekEvents.length,
      interviews: weekEvents.filter(e => e.type === 'interview').length,
      deadlines: weekEvents.filter(e => e.type === 'deadline' || e.type === 'offer_expiry').length,
    }
  }, [events, today])

  const completedThisWeek = useMemo(() =>
    followUps.filter(f => {
      if (!f.completedAt) return false
      const d = new Date(f.completedAt)
      const weekStart = new Date(today.getTime() - today.getDay() * 86400000)
      return d >= weekStart
    }).length,
  [followUps, today])

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Calendar className="h-4 w-4 text-primary" />
            Today's Schedule
          </CardTitle>
        </CardHeader>
        <CardContent>
          {todayEvents.length === 0 ? (
            <p className="text-xs text-muted-foreground">No events today</p>
          ) : (
            <div className="space-y-1.5">
              {todayEvents.slice(0, 4).map(e => (
                <div key={e.id} className="flex items-center gap-2 text-xs">
                  <div className={cn(
                    'w-1.5 h-1.5 rounded-full shrink-0',
                    e.type === 'interview' && 'bg-purple-400',
                    e.type === 'deadline' && 'bg-red-400',
                    e.type === 'follow_up' && 'bg-blue-400',
                  )} />
                  <span className="truncate">{e.title}</span>
                  {e.time && <span className="text-muted-foreground shrink-0">{e.time}</span>}
                </div>
              ))}
              {todayEvents.length > 4 && (
                <button onClick={onViewCalendar} className="text-xs text-primary hover:underline flex items-center gap-1">
                  <ArrowRight className="h-3 w-3" /> {todayEvents.length - 4} more
                </button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Target className="h-4 w-4 text-purple-400" />
            Upcoming Interviews
          </CardTitle>
        </CardHeader>
        <CardContent>
          {upcomingInterviews.length === 0 ? (
            <p className="text-xs text-muted-foreground">No upcoming interviews</p>
          ) : (
            <div className="space-y-1.5">
              {upcomingInterviews.map(e => (
                <div key={e.id} className="flex items-center gap-2 text-xs">
                  <div className="w-1.5 h-1.5 rounded-full bg-purple-400 shrink-0" />
                  <span className="truncate">{e.title}</span>
                  <span className="text-muted-foreground shrink-0">
                    {new Date(e.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-sm">
            <AlertTriangle className="h-4 w-4 text-amber-400" />
            Pending Follow-ups
          </CardTitle>
        </CardHeader>
        <CardContent>
          {pendingFollowUps.length === 0 ? (
            <p className="text-xs text-muted-foreground">All caught up!</p>
          ) : (
            <div className="space-y-1.5">
              {pendingFollowUps.slice(0, 4).map(f => (
                <div key={f.id} className="flex items-center gap-2 text-xs">
                  <div className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                  <span className="truncate">{f.title}</span>
                </div>
              ))}
              {pendingFollowUps.length > 4 && (
                <button onClick={onViewFollowUps} className="text-xs text-primary hover:underline flex items-center gap-1">
                  <ArrowRight className="h-3 w-3" /> {pendingFollowUps.length - 4} more
                </button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Clock className="h-4 w-4 text-red-400" />
            This Week's Deadlines
          </CardTitle>
        </CardHeader>
        <CardContent>
          {deadlines.length === 0 ? (
            <p className="text-xs text-muted-foreground">No deadlines this week</p>
          ) : (
            <div className="space-y-1.5">
              {deadlines.map(e => (
                <div key={e.id} className="flex items-center gap-2 text-xs">
                  <div className="w-1.5 h-1.5 rounded-full bg-red-400 shrink-0" />
                  <span className="truncate">{e.title}</span>
                  <span className="text-muted-foreground shrink-0">
                    {new Date(e.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-sm">
            <CheckCircle2 className="h-4 w-4 text-green-400" />
            Weekly Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div>
              <p className="text-lg font-semibold">{weeklyCount.total}</p>
              <p className="text-[10px] text-muted-foreground">Events</p>
            </div>
            <div>
              <p className="text-lg font-semibold">{weeklyCount.interviews}</p>
              <p className="text-[10px] text-muted-foreground">Interviews</p>
            </div>
            <div>
              <p className="text-lg font-semibold">{weeklyCount.deadlines}</p>
              <p className="text-[10px] text-muted-foreground">Deadlines</p>
            </div>
          </div>
          <div className="mt-2 text-center">
            <span className="text-xs text-muted-foreground">{completedThisWeek} follow-ups completed this week</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
