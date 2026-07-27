import { useQuery } from '@tanstack/react-query'
import { activityService } from '@/services/activity'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/layout/empty-state'
import { Activity, ArrowRight } from 'lucide-react'

interface ApplicationActivityProps {
  applicationId: string
}

export function ApplicationActivity({ applicationId }: ApplicationActivityProps) {
  const { data: entries, isLoading } = useQuery({
    queryKey: ['applications', applicationId, 'activity'],
    queryFn: () => activityService.list(applicationId),
    enabled: !!applicationId,
  })

  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle>Activity History</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </CardContent>
      </Card>
    )
  }

  if (!entries?.length) {
    return (
      <Card>
        <CardHeader><CardTitle>Activity History</CardTitle></CardHeader>
        <CardContent>
          <EmptyState icon={Activity} title="No activity yet" description="Changes to this application will be recorded here." />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader><CardTitle>Activity History</CardTitle></CardHeader>
      <CardContent>
        <div className="space-y-2" role="list" aria-label="Activity history">
          {entries.map(entry => (
            <div key={entry.id} className="flex items-start gap-3 p-2 rounded-lg hover:bg-dark-800/30 transition-colors" role="listitem">
              <Activity className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm">
                  <span className="font-medium capitalize">{entry.action.replace(/_/g, ' ')}</span>
                  {entry.field && (
                    <span className="text-muted-foreground"> on {entry.field.replace(/_/g, ' ')}</span>
                  )}
                </p>
                {(entry.old_value || entry.new_value) && (
                  <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                    {entry.old_value && <span className="line-through">{entry.old_value}</span>}
                    {entry.old_value && entry.new_value && <ArrowRight className="h-3 w-3" />}
                    {entry.new_value && <span>{entry.new_value}</span>}
                  </p>
                )}
                <p className="text-xs text-muted-foreground mt-0.5">
                  {new Date(entry.created_at).toLocaleString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
