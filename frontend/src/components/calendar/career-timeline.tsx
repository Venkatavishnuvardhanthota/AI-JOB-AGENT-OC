import { useState, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { cn } from '@/lib/utils'
import type { CalendarEvent, FollowUpTask, Reminder } from '@/services/calendar'
import type { Application } from '@/types'
import { Search, Calendar, Bell, AlertCircle, Target, FileText, ArrowRight } from 'lucide-react'

interface TimelineEntry {
  id: string
  date: string
  type: 'application_created' | 'application_update' | 'interview' | 'follow_up' | 'reminder' | 'deadline' | 'offer'
  title: string
  subtitle: string
  applicationId: string
  status?: string
}

interface CareerTimelineProps {
  applications: Application[]
  events: CalendarEvent[]
  followUps: FollowUpTask[]
  reminders: Reminder[]
}

export function CareerTimeline({ applications, events, followUps, reminders }: CareerTimelineProps) {
  const [search, setSearch] = useState('')
  const [filterType, setFilterType] = useState('all')

  const mergedTimeline = useMemo(() => {
    const entries: TimelineEntry[] = []

    for (const app of applications) {
      entries.push({
        id: `app_${app.id}`,
        date: app.created_at,
        type: 'application_created',
        title: `Applied: ${app.job_title}`,
        subtitle: app.company_name || '',
        applicationId: app.id,
        status: app.status,
      })
    }

    for (const event of events) {
      entries.push({
        id: `event_${event.id}`,
        date: event.date,
        type: event.type === 'interview' ? 'interview' : event.type === 'deadline' || event.type === 'offer_expiry' ? 'deadline' : 'application_update',
        title: event.title,
        subtitle: event.subtitle,
        applicationId: event.applicationId,
      })
    }

    for (const fu of followUps) {
      entries.push({
        id: `fu_${fu.id}`,
        date: fu.dueDate,
        type: 'follow_up',
        title: fu.title,
        subtitle: fu.description,
        applicationId: fu.applicationId,
      })
    }

    for (const rem of reminders) {
      entries.push({
        id: `rem_${rem.id}`,
        date: rem.dueDate,
        type: 'reminder',
        title: rem.title,
        subtitle: rem.description,
        applicationId: rem.applicationId,
      })
    }

    return entries.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
  }, [applications, events, followUps, reminders])

  const filtered = useMemo(() => {
    return mergedTimeline.filter(e => {
      if (search && !e.title.toLowerCase().includes(search.toLowerCase()) && !e.subtitle.toLowerCase().includes(search.toLowerCase())) return false
      if (filterType !== 'all' && e.type !== filterType) return false
      return true
    }).slice(0, 100)
  }, [mergedTimeline, search, filterType])

  const typeColors: Record<string, string> = {
    application_created: 'border-blue-500/30 bg-blue-500/10',
    application_update: 'border-green-500/30 bg-green-500/10',
    interview: 'border-purple-500/30 bg-purple-500/10',
    follow_up: 'border-amber-500/30 bg-amber-500/10',
    reminder: 'border-cyan-500/30 bg-cyan-500/10',
    deadline: 'border-red-500/30 bg-red-500/10',
    offer: 'border-emerald-500/30 bg-emerald-500/10',
  }

  const typeIcons: Record<string, React.ElementType> = {
    application_created: FileText,
    application_update: ArrowRight,
    interview: Target,
    follow_up: Bell,
    reminder: AlertCircle,
    deadline: Calendar,
    offer: Target,
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm">
          Career Timeline
          <Badge variant="outline" className="text-[10px]">{mergedTimeline.length} events</Badge>
        </CardTitle>
        <div className="flex items-center gap-2 mt-2">
          <div className="relative flex-1">
            <Search className="absolute left-2 top-2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search timeline..."
              className="pl-7 h-8 text-xs"
            />
          </div>
          <Select value={filterType} onChange={(e) => setFilterType(e.target.value)} className="w-28 h-8 text-xs" aria-label="Filter type">
            <option value="all">All Events</option>
            <option value="application_created">Applications</option>
            <option value="interview">Interviews</option>
            <option value="follow_up">Follow-ups</option>
            <option value="reminder">Reminders</option>
            <option value="deadline">Deadlines</option>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            <FileText className="h-8 w-8 mb-2 opacity-40" />
            <p className="text-sm">No timeline entries match your search</p>
          </div>
        ) : (
          <div className="relative">
            <div className="absolute left-4 top-0 bottom-0 w-px bg-glass-border" />
            <div className="space-y-0">
              {filtered.map((entry) => {
                const Icon = typeIcons[entry.type] || FileText
                return (
                  <div key={entry.id} className="relative flex items-start gap-4 pb-4 group">
                    <div className={cn(
                      'relative z-10 w-8 h-8 rounded-full flex items-center justify-center border',
                      typeColors[entry.type] || 'bg-dark-800 border-glass-border',
                    )}>
                      <Icon className="h-3.5 w-3.5" />
                    </div>
                    <div className="flex-1 min-w-0 pt-0.5">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium">{entry.title}</p>
                        <Badge variant="outline" className="text-[9px]">{entry.type.replace('_', ' ')}</Badge>
                      </div>
                      {entry.subtitle && (
                        <p className="text-xs text-muted-foreground">{entry.subtitle}</p>
                      )}
                      <p className="text-[10px] text-muted-foreground mt-0.5">
                        {new Date(entry.date).toLocaleDateString(undefined, {
                          weekday: 'short', year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
                        })}
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
