import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ApplicationStatusBadge } from './application-status-badge'
import { ApplicationPriorityBadge } from './application-priority-badge'
import { QuickActionsDropdown } from './quick-actions-dropdown'
import { getApplicationAge } from '@/hooks/useApplicationAge'
import { getReminderBadges } from '@/hooks/useReminderBadges'
import { Building2, MapPin, Calendar, DollarSign, User, Clock, FileText, FileSpreadsheet } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Application } from '@/types'

interface ApplicationCardProps {
  application: Application
  onAddNote?: (id: string) => void
}

export function ApplicationCard({ application, onAddNote }: ApplicationCardProps) {
  const age = getApplicationAge(application.created_at)
  const badges = getReminderBadges(application)

  return (
    <Card className={cn(
      "transition-colors hover:border-primary/50",
      age.isStale && "border-warning/30 opacity-80"
    )}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-medium truncate">{application.job_title}</h3>
              {badges.length > 0 && (
                <div className="flex gap-1 shrink-0">
                  {badges.slice(0, 2).map(b => (
                    <Badge key={b.type} variant={b.variant} className="text-[10px] px-1 py-0">
                      {b.label}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Building2 className="h-3.5 w-3.5" />
              <span>{application.company_name}</span>
            </div>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-xs text-muted-foreground">
              {application.location && (
                <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{application.location}</span>
              )}
              {application.salary && (
                <span className="flex items-center gap-1"><DollarSign className="h-3 w-3" />{application.salary}</span>
              )}
              {application.recruiter && (
                <span className="flex items-center gap-1"><User className="h-3 w-3" />{application.recruiter}</span>
              )}
              {application.deadline && (
                <span className={cn("flex items-center gap-1", new Date(application.deadline) < new Date() && "text-error")}>
                  <Calendar className="h-3 w-3" />Due {new Date(application.deadline).toLocaleDateString()}
                </span>
              )}
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />{age.label}
              </span>
              {application.resume_id && (
                <span className="flex items-center gap-1 text-primary/70"><FileSpreadsheet className="h-3 w-3" />Resume</span>
              )}
              {application.cover_letter_id && (
                <span className="flex items-center gap-1 text-secondary/70"><FileText className="h-3 w-3" />CL</span>
              )}
            </div>
          </div>
          <div className="flex flex-col items-end gap-2 shrink-0">
            <div className="flex items-center gap-2">
              <ApplicationStatusBadge status={application.status} />
              <QuickActionsDropdown application={application} onAddNote={onAddNote} />
            </div>
            <ApplicationPriorityBadge priority={application.priority} />
          </div>
        </div>
        <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
          <span>Updated {new Date(application.updated_at).toLocaleDateString()}</span>
        </div>
      </CardContent>
    </Card>
  )
}
