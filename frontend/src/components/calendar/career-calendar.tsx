import { useState, useMemo, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import type { CalendarEvent, CalendarView } from '@/services/calendar'
import { cn } from '@/lib/utils'
import { ChevronLeft, ChevronRight, Plus } from 'lucide-react'

interface CareerCalendarProps {
  events: CalendarEvent[]
  onScheduleInterview: (date: string) => void
}

const VIEWS: { value: CalendarView; label: string }[] = [
  { value: 'month', label: 'Month' },
  { value: 'week', label: 'Week' },
  { value: 'day', label: 'Day' },
  { value: 'agenda', label: 'Agenda' },
]

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

const eventColors: Record<string, string> = {
  interview: 'bg-purple-500/20 border-purple-500/30 text-purple-300',
  deadline: 'bg-red-500/20 border-red-500/30 text-red-300',
  offer_expiry: 'bg-amber-500/20 border-amber-500/30 text-amber-300',
  follow_up: 'bg-blue-500/20 border-blue-500/30 text-blue-300',
  reminder: 'bg-green-500/20 border-green-500/30 text-green-300',
  application: 'bg-primary/20 border-primary/30 text-primary-300',
  assessment: 'bg-cyan-500/20 border-cyan-500/30 text-cyan-300',
}

function getToday(): Date {
  const d = new Date()
  return new Date(d.getFullYear(), d.getMonth(), d.getDate())
}

function getDaysInMonth(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate()
}

function getFirstDayOfMonth(year: number, month: number): number {
  return new Date(year, month, 1).getDay()
}

export function CareerCalendar({ events, onScheduleInterview }: CareerCalendarProps) {
  const [view, setView] = useState<CalendarView>('month')
  const [currentDate, setCurrentDate] = useState(getToday())
  const [selectedDate, setSelectedDate] = useState(getToday())

  const year = currentDate.getFullYear()
  const month = currentDate.getMonth()
  const today = getToday()

  const eventMap = useMemo(() => {
    const map = new Map<string, CalendarEvent[]>()
    for (const e of events) {
      const key = new Date(e.date).toISOString().split('T')[0]
      if (!map.has(key)) map.set(key, [])
      map.get(key)!.push(e)
    }
    return map
  }, [events])

  const navigate = useCallback((delta: number) => {
    const d = new Date(currentDate)
    if (view === 'month') d.setMonth(d.getMonth() + delta)
    else if (view === 'week') d.setDate(d.getDate() + delta * 7)
    else d.setDate(d.getDate() + delta)
    setCurrentDate(d)
  }, [currentDate, view])

  const weekStart = useMemo(() => {
    const d = new Date(currentDate)
    d.setDate(d.getDate() - d.getDay())
    return d
  }, [currentDate])

  const weekDays = useMemo(() => {
    return Array.from({ length: 7 }, (_, i) => {
      const d = new Date(weekStart)
      d.setDate(d.getDate() + i)
      return d
    })
  }, [weekStart])

  const headerLabel = useMemo(() => {
    if (view === 'day') return `${MONTHS[month]} ${currentDate.getDate()}, ${year}`
    return `${MONTHS[month]} ${year}`
  }, [view, month, year, currentDate])

  const renderMonth = () => {
    const daysInMonth = getDaysInMonth(year, month)
    const firstDay = getFirstDayOfMonth(year, month)
    const days: (number | null)[] = Array(firstDay).fill(null)
    for (let i = 1; i <= daysInMonth; i++) days.push(i)

    return (
      <div className="grid grid-cols-7 gap-px bg-glass-border rounded-lg overflow-hidden">
        {DAYS.map(d => (
          <div key={d} className="bg-dark-800 px-2 py-1.5 text-xs font-medium text-muted-foreground text-center">{d}</div>
        ))}
        {days.map((day) => {
          if (day === null) return <div key={`e${day}_${Math.random()}`} className="bg-dark-900 min-h-[80px]" />
          const date = new Date(year, month, day)
          const key = date.toISOString().split('T')[0]
          const dayEvents = eventMap.get(key) || []
          const isToday = date.getTime() === today.getTime()
          const isSelected = date.getTime() === selectedDate.getTime()

          return (
            <div
              key={key}
              onClick={() => setSelectedDate(date)}
              className={cn(
                'bg-dark-900 min-h-[80px] p-1 cursor-pointer transition-colors hover:bg-dark-800',
                isToday && 'bg-primary/5',
                isSelected && 'ring-1 ring-primary/30',
              )}
            >
              <span className={cn(
                'text-xs inline-flex items-center justify-center w-5 h-5 rounded-full',
                isToday && 'bg-primary text-white font-medium',
              )}>
                {day}
              </span>
              <div className="space-y-0.5 mt-0.5">
                {dayEvents.slice(0, 3).map(e => (
                  <div
                    key={e.id}
                    className={cn(
                      'text-[9px] px-1 py-0.5 rounded truncate border',
                      eventColors[e.type] || 'bg-dark-700 border-glass-border text-muted-foreground',
                    )}
                    title={e.title}
                  >
                    {e.title}
                  </div>
                ))}
                {dayEvents.length > 3 && (
                  <span className="text-[9px] text-muted-foreground">+{dayEvents.length - 3} more</span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  const renderWeek = () => (
    <div className="grid grid-cols-7 gap-px bg-glass-border rounded-lg overflow-hidden min-h-[400px]">
      {DAYS.map(d => (
        <div key={d} className="bg-dark-800 px-2 py-1.5 text-xs font-medium text-muted-foreground text-center">{d}</div>
      ))}
      {weekDays.map(date => {
        const key = date.toISOString().split('T')[0]
        const dayEvents = eventMap.get(key) || []
        const isToday = date.getTime() === today.getTime()

        return (
          <div
            key={key}
            onClick={() => setSelectedDate(date)}
            className={cn(
              'bg-dark-900 min-h-[100px] p-1 cursor-pointer transition-colors hover:bg-dark-800',
              isToday && 'bg-primary/5',
            )}
          >
            <span className={cn(
              'text-xs inline-flex items-center justify-center w-5 h-5 rounded-full',
              isToday && 'bg-primary text-white font-medium',
            )}>
              {date.getDate()}
            </span>
            <div className="space-y-0.5 mt-0.5">
              {dayEvents.slice(0, 4).map(e => (
                <div
                  key={e.id}
                  className={cn(
                    'text-[9px] px-1 py-0.5 rounded truncate border',
                    eventColors[e.type] || 'bg-dark-700 border-glass-border text-muted-foreground',
                  )}
                  title={e.title}
                >
                  {e.title}
                </div>
              ))}
              {dayEvents.length > 4 && (
                <span className="text-[9px] text-muted-foreground">+{dayEvents.length - 4} more</span>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )

  const renderDay = () => {
    const key = selectedDate.toISOString().split('T')[0]
    const dayEvents = eventMap.get(key) || []
    const isToday = selectedDate.getTime() === today.getTime()

    return (
      <div className="space-y-3">
        <div className={cn(
          'text-sm font-medium px-3 py-2 rounded-lg',
          isToday ? 'bg-primary/10 text-primary' : 'bg-dark-800 text-foreground',
        )}>
          {MONTHS[selectedDate.getMonth()]} {selectedDate.getDate()}, {selectedDate.getFullYear()}
          {isToday && <Badge className="ml-2 text-[10px]">Today</Badge>}
        </div>
        {dayEvents.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">No events for this day</p>
        ) : (
          <div className="space-y-2">
            {dayEvents.map(e => (
              <div key={e.id} className={cn(
                'rounded-lg border p-3',
                eventColors[e.type] || 'bg-dark-800 border-glass-border',
              )}>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium">{e.title}</p>
                    <p className="text-xs text-muted-foreground">{e.subtitle}</p>
                    {e.time && <p className="text-xs text-muted-foreground mt-0.5">{e.time}</p>}
                    {e.meetingUrl && (
                      <a href={e.meetingUrl} target="_blank" rel="noopener noreferrer" className="text-xs text-primary hover:underline mt-1 inline-block">
                        Meeting link
                      </a>
                    )}
                  </div>
                  <Badge variant="outline" className="text-[10px]">{e.type.replace('_', ' ')}</Badge>
                </div>
                {e.notes && <p className="text-xs text-muted-foreground mt-2">{e.notes}</p>}
              </div>
            ))}
          </div>
        )}
        <Button variant="outline" size="sm" onClick={() => onScheduleInterview(key)}>
          <Plus className="h-3 w-3 mr-1" /> Schedule Interview
        </Button>
      </div>
    )
  }

  const renderAgenda = () => {
    const sorted = [...events].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    const upcoming = sorted.filter(e => new Date(e.date) >= today).slice(0, 30)
    const past = sorted.filter(e => new Date(e.date) < today).slice(-10).reverse()

    if (upcoming.length === 0 && past.length === 0) {
      return <p className="text-sm text-muted-foreground text-center py-8">No events</p>
    }

    return (
      <div className="space-y-6">
        {upcoming.length > 0 && (
          <div>
            <h3 className="text-sm font-medium mb-2 flex items-center gap-2">
              Upcoming
              <Badge variant="outline" className="text-[10px]">{upcoming.length}</Badge>
            </h3>
            <div className="space-y-1">
              {upcoming.map(e => (
                <div key={e.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-dark-800 transition-colors">
                  <div className="w-16 shrink-0 text-xs text-muted-foreground">
                    {new Date(e.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                  </div>
                  <div className={cn(
                    'w-2 h-2 rounded-full shrink-0',
                    e.type === 'interview' && 'bg-purple-400',
                    e.type === 'deadline' && 'bg-red-400',
                    e.type === 'offer_expiry' && 'bg-amber-400',
                    e.type === 'follow_up' && 'bg-blue-400',
                    e.type === 'reminder' && 'bg-green-400',
                    e.type === 'application' && 'bg-primary',
                  )} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm truncate">{e.title}</p>
                    <p className="text-xs text-muted-foreground truncate">{e.subtitle}</p>
                  </div>
                  {e.time && <span className="text-xs text-muted-foreground shrink-0">{e.time}</span>}
                  <Badge variant="outline" className="text-[10px] shrink-0">{e.type.replace('_', ' ')}</Badge>
                </div>
              ))}
            </div>
          </div>
        )}
        {past.length > 0 && (
          <div>
            <h3 className="text-sm font-medium mb-2 text-muted-foreground">Past</h3>
            <div className="space-y-1 opacity-60">
              {past.map(e => (
                <div key={e.id} className="flex items-center gap-3 p-2 rounded-lg">
                  <div className="w-16 shrink-0 text-xs text-muted-foreground">
                    {new Date(e.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                  </div>
                  <div className="w-2 h-2 rounded-full bg-dark-600 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm truncate line-through">{e.title}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            Career Calendar
            <Badge variant="outline" className="text-[10px]">{events.length} events</Badge>
          </CardTitle>
          <div className="flex items-center gap-2">
            <Select value={view} onChange={(e) => { setView(e.target.value as CalendarView) }} className="w-24 h-8 text-xs" aria-label="Calendar view">
              {VIEWS.map(v => <option key={v.value} value={v.value}>{v.label}</option>)}
            </Select>
          </div>
        </div>
        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => navigate(-1)} aria-label="Previous">
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-sm font-medium min-w-[160px] text-center">{headerLabel}</span>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => navigate(1)} aria-label="Next">
              <ChevronRight className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm" className="h-7 text-xs" onClick={() => setCurrentDate(getToday())}>
              Today
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {view === 'month' && renderMonth()}
        {view === 'week' && renderWeek()}
        {view === 'day' && renderDay()}
        {view === 'agenda' && renderAgenda()}
      </CardContent>
    </Card>
  )
}
