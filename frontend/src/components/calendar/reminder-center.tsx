import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { calendarService } from '@/services/calendar'
import { cn } from '@/lib/utils'
import { Bell, CheckCircle2, Clock, AlertCircle, Archive, X, Calendar } from 'lucide-react'

interface ReminderCenterProps {
  onUpdate: () => void
}

type ReminderTab = 'today' | 'upcoming' | 'overdue' | 'completed' | 'dismissed'

const TABS: { key: ReminderTab; label: string }[] = [
  { key: 'today', label: 'Today' },
  { key: 'upcoming', label: 'Upcoming' },
  { key: 'overdue', label: 'Overdue' },
  { key: 'completed', label: 'Completed' },
  { key: 'dismissed', label: 'Dismissed' },
]

export function ReminderCenter({ onUpdate }: ReminderCenterProps) {
  const [activeTab, setActiveTab] = useState<ReminderTab>('today')

  const categorized = calendarService.categorizeReminders()

  const currentList = categorized[activeTab]

  const handleComplete = (id: string) => {
    calendarService.updateReminder(id, { category: 'completed', completedAt: new Date().toISOString() })
    onUpdate()
  }

  const handleDismiss = (id: string) => {
    calendarService.updateReminder(id, { category: 'dismissed' })
    onUpdate()
  }

  const handleArchive = (id: string) => {
    calendarService.updateReminder(id, { category: 'dismissed' })
    onUpdate()
  }

  const tabCounts = {
    today: categorized.today.length,
    upcoming: categorized.upcoming.length,
    overdue: categorized.overdue.length,
    completed: categorized.completed.length,
    dismissed: categorized.dismissed.length,
  }

  const totalActive = tabCounts.today + tabCounts.upcoming + tabCounts.overdue

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm">
          <Bell className="h-4 w-4 text-primary" /> Reminder Center
          {totalActive > 0 && <Badge variant="warning" className="text-[10px]">{totalActive} active</Badge>}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex gap-1 overflow-x-auto pb-2 mb-3">
          {TABS.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={cn(
                'px-2.5 py-1 text-xs rounded-lg whitespace-nowrap transition-colors',
                activeTab === tab.key
                  ? 'bg-primary/10 text-primary border border-primary/30'
                  : 'bg-dark-800 text-muted-foreground border border-glass-border hover:text-foreground',
              )}
            >
              {tab.label}
              {tabCounts[tab.key] > 0 && (
                <span className="ml-1 text-[9px] opacity-60">({tabCounts[tab.key]})</span>
              )}
            </button>
          ))}
        </div>

        {currentList.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            <Bell className="h-8 w-8 mb-2 opacity-40" />
            <p className="text-sm">No reminders in this category</p>
          </div>
        ) : (
          <div className="space-y-2">
            {currentList.map(reminder => {
              const dueDate = new Date(reminder.dueDate)
              const now = new Date()
              const isOverdue = dueDate < now

              return (
                <div
                  key={reminder.id}
                  className={cn(
                    'flex items-start gap-3 rounded-lg border p-3 transition-colors',
                    isOverdue && activeTab !== 'overdue' && 'border-red-500/20 bg-red-500/5',
                    activeTab === 'completed' && 'opacity-60',
                  )}
                >
                  <div className="mt-0.5">
                    {activeTab === 'overdue' || isOverdue ? (
                      <AlertCircle className="h-4 w-4 text-red-400" />
                    ) : (
                      <Clock className="h-4 w-4 text-amber-400" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{reminder.title}</p>
                    <p className="text-xs text-muted-foreground">{reminder.description}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Calendar className="h-2.5 w-2.5 text-muted-foreground" />
                      <span className="text-[10px] text-muted-foreground">
                        {dueDate.toLocaleDateString()}
                        {isOverdue && ` (${Math.floor((now.getTime() - dueDate.getTime()) / 86400000)}d overdue)`}
                      </span>
                    </div>
                  </div>
                  {activeTab !== 'completed' && activeTab !== 'dismissed' && (
                    <div className="flex items-center gap-1 shrink-0">
                      <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => handleComplete(reminder.id)} aria-label="Complete">
                        <CheckCircle2 className="h-3 w-3 text-green-400" />
                      </Button>
                      <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => handleDismiss(reminder.id)} aria-label="Dismiss">
                        <X className="h-3 w-3 text-muted-foreground" />
                      </Button>
                    </div>
                  )}
                  {activeTab === 'completed' && (
                    <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => handleArchive(reminder.id)} aria-label="Archive">
                      <Archive className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
