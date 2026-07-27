import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { calendarService, type FollowUpTask } from '@/services/calendar'
import { cn } from '@/lib/utils'
import { CheckCircle2, Clock, Bell, ChevronDown, ChevronUp, X } from 'lucide-react'

interface FollowUpPlannerProps {
  tasks: FollowUpTask[]
  onUpdate: () => void
}

const typeLabels: Record<string, string> = {
  after_application: 'Application Follow-up',
  after_interview: 'Post-Interview Thank You',
  assessment_reminder: 'Assessment Reminder',
  offer_reminder: 'Offer Follow-up',
  recruiter_followup: 'Recruiter Follow-up',
}

export function FollowUpPlanner({ tasks, onUpdate }: FollowUpPlannerProps) {
  const [showCompleted, setShowCompleted] = useState(false)

  const pending = tasks.filter(t => t.status === 'pending')
  const completed = tasks.filter(t => t.status === 'completed')

  const handleComplete = (id: string) => {
    calendarService.completeFollowUp(id)
    onUpdate()
  }

  const handleDismiss = (id: string) => {
    calendarService.updateFollowUp(id, { status: 'dismissed' })
    onUpdate()
  }

  if (tasks.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <Bell className="h-4 w-4 text-primary" /> Follow-up Planner
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-6">
            No follow-up tasks yet. They will be generated automatically as you apply to jobs.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm">
          <Bell className="h-4 w-4 text-primary" /> Follow-up Planner
          {pending.length > 0 && <Badge variant="warning" className="text-[10px]">{pending.length} pending</Badge>}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {pending.map(task => {
          const dueDate = new Date(task.dueDate)
          const now = new Date()
          const isOverdue = dueDate < now

          return (
            <div
              key={task.id}
              className={cn(
                'flex items-start gap-3 rounded-lg border p-3 transition-colors',
                isOverdue ? 'border-red-500/20 bg-red-500/5' : 'border-glass-border bg-dark-800',
              )}
            >
              <button
                onClick={() => handleComplete(task.id)}
                className="mt-0.5 p-0.5 hover:text-green-400 transition-colors"
                aria-label="Mark complete"
              >
                <CheckCircle2 className="h-4 w-4 text-muted-foreground hover:text-green-400" />
              </button>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium">{task.title}</p>
                  <Badge variant="outline" className="text-[9px]">{typeLabels[task.type] || task.type}</Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-0.5">{task.description}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className={cn(
                    'text-[10px] flex items-center gap-0.5',
                    isOverdue ? 'text-red-400' : 'text-muted-foreground',
                  )}>
                    <Clock className="h-2.5 w-2.5" />
                    Due: {dueDate.toLocaleDateString()}
                    {isOverdue && ` (${Math.floor((now.getTime() - dueDate.getTime()) / 86400000)}d overdue)`}
                  </span>
                </div>
              </div>
              <Button variant="ghost" size="icon" className="h-6 w-6 shrink-0" onClick={() => handleDismiss(task.id)} aria-label="Dismiss">
                <X className="h-3 w-3" />
              </Button>
            </div>
          )
        })}

        {completed.length > 0 && (
          <div>
            <button
              onClick={() => setShowCompleted(!showCompleted)}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors mt-3"
            >
              {showCompleted ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              {completed.length} completed
            </button>
            {showCompleted && (
              <div className="space-y-1 mt-2">
                {completed.map(task => (
                  <div key={task.id} className="flex items-center gap-2 text-xs text-muted-foreground opacity-60">
                    <CheckCircle2 className="h-3 w-3 text-green-400" />
                    <span className="truncate line-through">{task.title}</span>
                    {task.completedAt && <span className="shrink-0">{new Date(task.completedAt).toLocaleDateString()}</span>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
