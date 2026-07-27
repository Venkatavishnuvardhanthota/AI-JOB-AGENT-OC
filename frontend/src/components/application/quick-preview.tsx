import { useEffect, useRef } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ApplicationStatusBadge } from './application-status-badge'
import { ApplicationPriorityBadge } from './application-priority-badge'
import { getApplicationAge } from '@/hooks/useApplicationAge'
import { getReminderBadges } from '@/hooks/useReminderBadges'
import { Building2, MapPin, Calendar, DollarSign, User, Clock, FileSpreadsheet, FileText, X } from 'lucide-react'
import type { Application } from '@/types'

interface QuickPreviewProps {
  application: Application
  onClose: () => void
}

export function QuickPreview({ application, onClose }: QuickPreviewProps) {
  const ref = useRef<HTMLDivElement>(null)
  const age = getApplicationAge(application.created_at)
  const badges = getReminderBadges(application)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onClose()
      }
    }
    const keyHandler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('mousedown', handler)
    document.addEventListener('keydown', keyHandler)
    return () => {
      document.removeEventListener('mousedown', handler)
      document.removeEventListener('keydown', keyHandler)
    }
  }, [onClose])

  return (
    <div ref={ref} className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" role="dialog" aria-label="Application preview">
      <Card className="w-full max-w-md mx-4 max-h-[80vh] overflow-y-auto animate-in zoom-in-95 duration-150">
        <CardContent className="p-5">
          <div className="flex items-start justify-between mb-3">
            <div>
              <h3 className="font-semibold text-lg">{application.job_title}</h3>
              <p className="text-sm text-muted-foreground flex items-center gap-1 mt-0.5">
                <Building2 className="h-3.5 w-3.5" />{application.company_name}
              </p>
            </div>
            <button onClick={onClose} className="p-1 hover:bg-dark-700 rounded transition-colors" aria-label="Close preview">
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="flex flex-wrap gap-2 mb-4">
            <ApplicationStatusBadge status={application.status} />
            <ApplicationPriorityBadge priority={application.priority} />
            <Badge variant="outline" className="text-muted-foreground text-xs">
              <Clock className="h-3 w-3 mr-1" />{age.label}
            </Badge>
            {badges.slice(0, 3).map(b => (
              <Badge key={b.type} variant={b.variant} className="text-xs">{b.label}</Badge>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-3 text-sm">
            {application.location && (
              <div><p className="text-xs text-muted-foreground">Location</p><p className="flex items-center gap-1"><MapPin className="h-3 w-3" />{application.location}</p></div>
            )}
            {application.salary && (
              <div><p className="text-xs text-muted-foreground">Salary</p><p className="flex items-center gap-1"><DollarSign className="h-3 w-3" />{application.salary}</p></div>
            )}
            {application.recruiter && (
              <div><p className="text-xs text-muted-foreground">Recruiter</p><p className="flex items-center gap-1"><User className="h-3 w-3" />{application.recruiter}</p></div>
            )}
            {application.deadline && (
              <div><p className="text-xs text-muted-foreground">Deadline</p><p className="flex items-center gap-1"><Calendar className="h-3 w-3" />{new Date(application.deadline).toLocaleDateString()}</p></div>
            )}
          </div>

          <div className="flex flex-wrap gap-3 mt-4 text-xs text-muted-foreground border-t border-glass-border pt-3">
            {application.resume_id && (
              <span className="flex items-center gap-1"><FileSpreadsheet className="h-3 w-3 text-primary/60" />Resume attached</span>
            )}
            {application.cover_letter_id && (
              <span className="flex items-center gap-1"><FileText className="h-3 w-3 text-secondary/60" />Cover letter attached</span>
            )}
            {application.source && (
              <span>Source: {application.source}</span>
            )}
            {application.work_type && (
              <span>Work type: {application.work_type}</span>
            )}
          </div>

          <div className="mt-4 pt-3 border-t border-glass-border text-xs text-muted-foreground space-y-1">
            <p>Created: {new Date(application.created_at).toLocaleDateString()}</p>
            <p>Updated: {new Date(application.updated_at).toLocaleDateString()}</p>
            {application.applied_date && <p>Applied: {new Date(application.applied_date).toLocaleDateString()}</p>}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
