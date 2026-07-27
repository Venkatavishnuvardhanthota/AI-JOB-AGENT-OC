import type { Application, ApplicationStatus } from '@/types'

const PREFIX = 'ajapp_cal_'

export type CalendarView = 'month' | 'week' | 'day' | 'agenda'

export interface CalendarEvent {
  id: string
  applicationId: string
  title: string
  subtitle: string
  date: string
  endDate?: string
  time?: string
  endTime?: string
  timezone?: string
  type: 'interview' | 'assessment' | 'deadline' | 'offer_expiry' | 'follow_up' | 'reminder' | 'application'
  status: 'scheduled' | 'completed' | 'cancelled' | 'rescheduled'
  platform?: string
  meetingUrl?: string
  recruiter?: string
  interviewer?: string
  notes?: string
  preparationNotes?: string
  applicationStatus?: ApplicationStatus
  priority?: string
  companyName?: string
}

export interface FollowUpTask {
  id: string
  applicationId: string
  title: string
  description: string
  dueDate: string
  type: 'after_application' | 'after_interview' | 'assessment_reminder' | 'offer_reminder' | 'recruiter_followup'
  status: 'pending' | 'completed' | 'dismissed' | 'rescheduled'
  intervalDays: number
  recurring: boolean
  createdAt: string
  completedAt?: string
}

export interface Reminder {
  id: string
  applicationId: string
  title: string
  description: string
  dueDate: string
  category: 'today' | 'upcoming' | 'overdue' | 'completed' | 'dismissed'
  createdAt: string
  completedAt?: string
}

function get<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(PREFIX + key)
    return raw ? JSON.parse(raw) : fallback
  } catch { return fallback }
}

function set<T>(key: string, value: T): void {
  try { localStorage.setItem(PREFIX + key, JSON.stringify(value)) } catch {}
}

export const calendarService = {
  getEvents(): CalendarEvent[] {
    return get<CalendarEvent[]>('events', [])
  },

  setEvents(events: CalendarEvent[]): void {
    set('events', events)
  },

  addEvent(event: CalendarEvent): CalendarEvent[] {
    const events = this.getEvents()
    events.push(event)
    this.setEvents(events)
    return events
  },

  updateEvent(id: string, updates: Partial<CalendarEvent>): CalendarEvent[] {
    const events = this.getEvents().map(e => e.id === id ? { ...e, ...updates } : e)
    this.setEvents(events)
    return events
  },

  deleteEvent(id: string): CalendarEvent[] {
    const events = this.getEvents().filter(e => e.id !== id)
    this.setEvents(events)
    return events
  },

  syncFromApplications(applications: Application[]): CalendarEvent[] {
    const existing = this.getEvents()
    const existingIds = new Set(existing.map(e => e.id))

    const newEvents: CalendarEvent[] = []

    for (const app of applications) {
      const eventId = `app_${app.id}`

      if (!existingIds.has(eventId)) {
        newEvents.push({
          id: eventId,
          applicationId: app.id,
          title: app.job_title,
          subtitle: app.company_name,
          date: app.created_at,
          type: 'application',
          status: 'scheduled',
          applicationStatus: app.status,
          priority: app.priority,
          companyName: app.company_name,
        })
      }

      if (app.applied_date) {
        const appliedId = `applied_${app.id}`
        if (!existingIds.has(appliedId)) {
          newEvents.push({
            id: appliedId,
            applicationId: app.id,
            title: `Applied: ${app.job_title}`,
            subtitle: app.company_name,
            date: app.applied_date,
            type: 'application',
            status: 'completed',
            applicationStatus: app.status,
            companyName: app.company_name,
          })
        }
      }

      if (app.deadline) {
        const deadlineId = `deadline_${app.id}`
        if (!existingIds.has(deadlineId)) {
          newEvents.push({
            id: deadlineId,
            applicationId: app.id,
            title: `Deadline: ${app.job_title}`,
            subtitle: app.company_name,
            date: app.deadline,
            type: 'deadline',
            status: 'scheduled',
            applicationStatus: app.status,
            companyName: app.company_name,
          })
        }
      }
    }

    const merged = [...existing, ...newEvents]
    this.setEvents(merged)
    return merged
  },

  getEventsForDate(date: Date): CalendarEvent[] {
    const dateStr = date.toISOString().split('T')[0]
    return this.getEvents().filter(e => {
      const eventDate = new Date(e.date).toISOString().split('T')[0]
      return eventDate === dateStr
    }).sort((a, b) => {
      if (a.time && b.time) return a.time.localeCompare(b.time)
      if (a.time) return -1
      if (b.time) return 1
      return 0
    })
  },

  getEventsForMonth(year: number, month: number): Map<string, CalendarEvent[]> {
    const events = this.getEvents()
    const map = new Map<string, CalendarEvent[]>()
    for (const e of events) {
      const d = new Date(e.date)
      if (d.getFullYear() === year && d.getMonth() === month) {
        const key = d.toISOString().split('T')[0]
        if (!map.has(key)) map.set(key, [])
        map.get(key)!.push(e)
      }
    }
    return map
  },

  getEventsForRange(from: Date, to: Date): CalendarEvent[] {
    const fromTime = from.getTime()
    const toTime = to.getTime()
    return this.getEvents().filter(e => {
      const t = new Date(e.date).getTime()
      return t >= fromTime && t <= toTime
    }).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
  },

  getUpcomingEvents(days: number = 30): CalendarEvent[] {
    const now = new Date()
    const future = new Date(now.getTime() + days * 86400000)
    return this.getEventsForRange(now, future).filter(e => e.status === 'scheduled')
  },

  getTodayEvents(): CalendarEvent[] {
    return this.getEventsForDate(new Date())
  },

  getInterviews(): CalendarEvent[] {
    return this.getEvents().filter(e =>
      e.type === 'interview' && e.status === 'scheduled'
    ).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
  },

  getFollowUps(): FollowUpTask[] {
    return get<FollowUpTask[]>('followups', [])
  },

  setFollowUps(tasks: FollowUpTask[]): void {
    set('followups', tasks)
  },

  addFollowUp(task: FollowUpTask): FollowUpTask[] {
    const tasks = this.getFollowUps()
    tasks.push(task)
    this.setFollowUps(tasks)
    return tasks
  },

  updateFollowUp(id: string, updates: Partial<FollowUpTask>): FollowUpTask[] {
    const tasks = this.getFollowUps().map(t => t.id === id ? { ...t, ...updates } : t)
    this.setFollowUps(tasks)
    return tasks
  },

  completeFollowUp(id: string): FollowUpTask[] {
    return this.updateFollowUp(id, { status: 'completed', completedAt: new Date().toISOString() })
  },

  generateFollowUpsFromApplications(applications: Application[]): FollowUpTask[] {
    const existing = this.getFollowUps()
    const existingSet = new Set(existing.map(t => `${t.applicationId}_${t.type}`))
    const newTasks: FollowUpTask[] = []

    for (const app of applications) {
      const key = `${app.id}_after_application`
      if (!existingSet.has(key) && (app.status === 'applied' || app.status === 'application_viewed')) {
        newTasks.push({
          id: `fu_${app.id}_${Date.now()}`,
          applicationId: app.id,
          title: `Follow up: ${app.job_title}`,
          description: `Follow up on application to ${app.company_name}`,
          dueDate: new Date(Date.now() + 7 * 86400000).toISOString(),
          type: 'after_application',
          status: 'pending',
          intervalDays: 7,
          recurring: false,
          createdAt: new Date().toISOString(),
        })
      }

      const intKey = `${app.id}_after_interview`
      if (!existingSet.has(intKey) && ['technical_interview', 'hr_interview', 'final_interview'].includes(app.status)) {
        newTasks.push({
          id: `fu_${app.id}_interview_${Date.now()}`,
          applicationId: app.id,
          title: `Thank you note: ${app.job_title}`,
          description: `Send thank you note to recruiter at ${app.company_name}`,
          dueDate: new Date(Date.now() + 1 * 86400000).toISOString(),
          type: 'after_interview',
          status: 'pending',
          intervalDays: 1,
          recurring: false,
          createdAt: new Date().toISOString(),
        })
      }
    }

    const merged = [...existing, ...newTasks]
    this.setFollowUps(merged)
    return merged
  },

  getReminders(): Reminder[] {
    return get<Reminder[]>('reminders', [])
  },

  setReminders(reminders: Reminder[]): void {
    set('reminders', reminders)
  },

  addReminder(reminder: Reminder): Reminder[] {
    const reminders = this.getReminders()
    reminders.push(reminder)
    this.setReminders(reminders)
    return reminders
  },

  updateReminder(id: string, updates: Partial<Reminder>): Reminder[] {
    const reminders = this.getReminders().map(r => r.id === id ? { ...r, ...updates } : r)
    this.setReminders(reminders)
    return reminders
  },

  categorizeReminders(): { today: Reminder[]; upcoming: Reminder[]; overdue: Reminder[]; completed: Reminder[]; dismissed: Reminder[] } {
    const all = this.getReminders()
    const now = new Date()
    const todayEnd = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59)

    return {
      today: all.filter(r => {
        const d = new Date(r.dueDate)
        return r.category !== 'completed' && r.category !== 'dismissed' && d <= todayEnd && d >= new Date(now.getFullYear(), now.getMonth(), now.getDate())
      }),
      upcoming: all.filter(r => {
        const d = new Date(r.dueDate)
        return r.category !== 'completed' && r.category !== 'dismissed' && d > todayEnd
      }),
      overdue: all.filter(r => {
        const d = new Date(r.dueDate)
        return r.category !== 'completed' && r.category !== 'dismissed' && d < new Date(now.getFullYear(), now.getMonth(), now.getDate())
      }),
      completed: all.filter(r => r.category === 'completed'),
      dismissed: all.filter(r => r.category === 'dismissed'),
    }
  },

  generateRemindersFromApplications(applications: Application[]): Reminder[] {
    const existing = this.getReminders()
    const existingSet = new Set(existing.map(r => `${r.applicationId}_${r.title}`))
    const newReminders: Reminder[] = []

    for (const app of applications) {
      if (app.deadline) {
        const key = `${app.id}_deadline_${app.job_title}`
        if (!existingSet.has(key)) {
          const deadlineDate = new Date(app.deadline)
          const daysUntil = Math.ceil((deadlineDate.getTime() - Date.now()) / 86400000)
          newReminders.push({
            id: `rem_${app.id}_deadline_${Date.now()}`,
            applicationId: app.id,
            title: `Deadline approaching: ${app.job_title}`,
            description: `${app.job_title} at ${app.company_name} deadline is ${daysUntil > 0 ? `in ${daysUntil} days` : 'today'}`,
            dueDate: app.deadline,
            category: daysUntil <= 0 ? 'overdue' : daysUntil <= 3 ? 'today' : 'upcoming',
            createdAt: new Date().toISOString(),
          })
        }
      }

      const interviewStatuses: ApplicationStatus[] = ['technical_interview', 'hr_interview', 'final_interview']
      if (interviewStatuses.includes(app.status)) {
        const key = `${app.id}_interview_${app.job_title}`
        if (!existingSet.has(key)) {
          newReminders.push({
            id: `rem_${app.id}_interview_${Date.now()}`,
            applicationId: app.id,
            title: `Interview: ${app.job_title}`,
            description: `Interview for ${app.job_title} at ${app.company_name}`,
            dueDate: new Date(Date.now() + 3 * 86400000).toISOString(),
            category: 'upcoming',
            createdAt: new Date().toISOString(),
          })
        }
      }

      const daysSinceUpdate = Math.floor((Date.now() - new Date(app.updated_at).getTime()) / 86400000)
      if (daysSinceUpdate >= 14 && !['accepted', 'rejected', 'withdrawn', 'archived'].includes(app.status)) {
        const key = `${app.id}_followup_${app.job_title}`
        if (!existingSet.has(key)) {
          newReminders.push({
            id: `rem_${app.id}_followup_${Date.now()}`,
            applicationId: app.id,
            title: `Follow up: ${app.job_title}`,
            description: `No update on ${app.job_title} at ${app.company_name} for ${daysSinceUpdate} days`,
            dueDate: new Date().toISOString(),
            category: 'overdue',
            createdAt: new Date().toISOString(),
          })
        }
      }
    }

    const merged = [...existing, ...newReminders]
    this.setReminders(merged)
    return merged
  },
}

export const interviewService = {
  scheduleInterview(event: Omit<CalendarEvent, 'id' | 'type' | 'status'>): CalendarEvent {
    const newEvent: CalendarEvent = {
      ...event,
      id: `int_${event.applicationId}_${Date.now()}`,
      type: 'interview',
      status: 'scheduled',
    }
    calendarService.addEvent(newEvent)
    return newEvent
  },

  rescheduleInterview(eventId: string, newDate: string, newTime?: string): CalendarEvent[] {
    return calendarService.updateEvent(eventId, { date: newDate, time: newTime, status: 'rescheduled' })
  },

  cancelInterview(eventId: string): CalendarEvent[] {
    return calendarService.updateEvent(eventId, { status: 'cancelled' })
  },

  completeInterview(eventId: string): CalendarEvent[] {
    return calendarService.updateEvent(eventId, { status: 'completed' })
  },
}
