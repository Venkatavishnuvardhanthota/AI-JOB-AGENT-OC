import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useSavedJobs } from '@/api/hooks'
import { PageHeader } from '@/components/layout/page-header'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/layout/empty-state'
import { Eye, MapPin, DollarSign, Clock } from 'lucide-react'
import { timeAgo, formatSalary } from '@/lib/utils'

export function SavedJobsPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useSavedJobs({ page, page_size: 20 })

  const items = (data as any)?.items || []
  const total = (data as any)?.total || 0
  const totalPages = (data as any)?.total_pages || 1

  if (isLoading) return <div className="space-y-4">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}</div>

  if (!isLoading && items.length === 0) {
    return (
      <EmptyState
        icon={Eye}
        title="No saved jobs"
        description="Save jobs you're interested in to track them here."
        action={<Link to="/jobs/search"><Button>Search Jobs</Button></Link>}
      />
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Saved Jobs" description={`${total} saved job${total !== 1 ? 's' : ''}`} />

      <div className="space-y-3">
        {items.map((job: any) => (
          <Link key={job.id} to={`/jobs/${job.id}`}>
            <Card className="hover:bg-white/[0.03] transition-colors">
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <h3 className="font-semibold">{job.title}</h3>
                    <p className="text-sm text-muted-foreground">{job.company_name}</p>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{job.remote ? 'Remote' : job.location || '-'}</span>
                      <span className="flex items-center gap-1"><DollarSign className="h-3 w-3" />{formatSalary(job.salary_min, job.salary_max)}</span>
                      <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{timeAgo(job.posted_at)}</span>
                    </div>
                  </div>
                  <Badge variant="secondary">{job.source}</Badge>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Previous</Button>
          <span className="text-sm text-muted-foreground self-center">Page {page} of {totalPages}</span>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next</Button>
        </div>
      )}
    </div>
  )
}
