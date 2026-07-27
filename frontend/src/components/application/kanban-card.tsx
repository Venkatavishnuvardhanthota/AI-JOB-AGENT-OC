import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Badge } from '@/components/ui/badge'
import { ApplicationStatusBadge } from './application-status-badge'
import { ApplicationPriorityBadge } from './application-priority-badge'
import { getApplicationAge } from '@/hooks/useApplicationAge'
import { getReminderBadges } from '@/hooks/useReminderBadges'
import { Building2, MapPin, Calendar, DollarSign, User, Clock, FileSpreadsheet, FileText, GripVertical } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Application } from '@/types'

interface KanbanCardProps {
  application: Application
  isDragging?: boolean
  onDragStart?: (e: React.DragEvent) => void
  onDragEnd?: (e: React.DragEvent) => void
  onPreview?: (application: Application) => void
  selected?: boolean
  onSelect?: (id: string, shiftKey: boolean) => void
}

export function KanbanCard({ application, isDragging, onDragStart, onDragEnd, onPreview, selected, onSelect }: KanbanCardProps) {
  const navigate = useNavigate()
  const age = getApplicationAge(application.created_at)
  const badges = getReminderBadges(application)

  const handleClick = useCallback((e: React.MouseEvent) => {
    if (onSelect && e.shiftKey) {
      e.preventDefault()
      onSelect(application.id, true)
      return
    }
    if (onPreview && !e.ctrlKey && !e.metaKey) {
      e.preventDefault()
      onPreview(application)
    }
  }, [application.id, onPreview, onSelect])

  const handleDoubleClick = useCallback(() => {
    navigate(`/applications/${application.id}`)
  }, [navigate, application.id])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      navigate(`/applications/${application.id}`)
    }
    if (e.key === ' ' && onSelect) {
      e.preventDefault()
      onSelect(application.id, e.shiftKey)
    }
  }, [navigate, application.id, onSelect])

  return (
    <div
      draggable
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="button"
      aria-label={`${application.job_title} at ${application.company_name}. Status: ${application.status}. Priority: ${application.priority}`}
      className={cn(
        'group rounded-lg border bg-dark-800 p-3 cursor-pointer transition-all duration-150 select-none',
        'hover:border-primary/40 hover:shadow-md hover:shadow-primary/5',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50',
        isDragging && 'opacity-50 shadow-lg scale-105 rotate-1 border-primary/50',
        selected && 'ring-2 ring-primary/60 border-primary/60',
        age.isStale && 'border-warning/20 opacity-80',
      )}
    >
      <div className="flex items-start gap-2">
        <div className="mt-0.5 cursor-grab active:cursor-grabbing opacity-0 group-hover:opacity-100 transition-opacity" aria-hidden="true">
          <GripVertical className="h-3.5 w-3.5 text-muted-foreground" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 mb-1">
            <span className="text-sm font-medium truncate">{application.job_title}</span>
            {badges.length > 0 && (
              <div className="flex gap-1 shrink-0">
                {badges.slice(0, 1).map(b => (
                  <Badge key={b.type} variant={b.variant} className="text-[9px] px-1 py-0 leading-3">{b.label}</Badge>
                ))}
              </div>
            )}
          </div>
          <div className="flex items-center gap-1 text-xs text-muted-foreground mb-2">
            <Building2 className="h-3 w-3" />
            <span className="truncate">{application.company_name}</span>
          </div>
          <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[11px] text-muted-foreground">
            {application.location && (
              <span className="flex items-center gap-0.5"><MapPin className="h-2.5 w-2.5" />{application.location}</span>
            )}
            {application.salary && (
              <span className="flex items-center gap-0.5"><DollarSign className="h-2.5 w-2.5" />{application.salary}</span>
            )}
            {application.recruiter && (
              <span className="flex items-center gap-0.5"><User className="h-2.5 w-2.5" />{application.recruiter}</span>
            )}
            {application.deadline && (
              <span className={cn('flex items-center gap-0.5', new Date(application.deadline) < new Date() && 'text-error')}>
                <Calendar className="h-2.5 w-2.5" />{new Date(application.deadline).toLocaleDateString()}
              </span>
            )}
            <span className="flex items-center gap-0.5"><Clock className="h-2.5 w-2.5" />{age.label}</span>
          </div>
          {application.resume_id && (
            <div className="flex items-center gap-1 mt-1.5">
              {application.resume_id && <FileSpreadsheet className="h-3 w-3 text-primary/60" />}
              {application.cover_letter_id && <FileText className="h-3 w-3 text-secondary/60" />}
            </div>
          )}
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          <ApplicationPriorityBadge priority={application.priority} />
          <ApplicationStatusBadge status={application.status} />
        </div>
      </div>
    </div>
  )
}
