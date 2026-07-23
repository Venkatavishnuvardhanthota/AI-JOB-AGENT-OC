import { useState } from 'react'
import { useApplications, useSubmitApplication, useCancelApplication } from '@/api/hooks'
import { PageHeader } from '@/components/layout/page-header'
import { DataTable, type Column } from '@/components/layout/data-table'
import { EmptyState } from '@/components/layout/empty-state'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/components/ui/toast'
import { FileText, Send, XCircle, ExternalLink } from 'lucide-react'
import { Link } from 'react-router-dom'

interface Application {
  id: string
  job_id: string
  job_title?: string
  company_name?: string
  status: string
  created_at: string
  submitted_at?: string
}

export function ApplicationsPage() {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const { data, isLoading } = useApplications({ status: statusFilter || undefined, page, page_size: 20 })
  const submitApp = useSubmitApplication()
  const cancelApp = useCancelApplication()
  const { addToast } = useToast()

  const items: Application[] = (data as any)?.items || []

  const handleSubmit = async (id: string) => {
    try {
      await submitApp.mutateAsync(id)
      addToast('Application submitted!', 'success')
    } catch {
      addToast('Failed to submit application', 'error')
    }
  }

  const handleCancel = async (id: string) => {
    try {
      await cancelApp.mutateAsync(id)
      addToast('Application cancelled', 'info')
    } catch {
      addToast('Failed to cancel application', 'error')
    }
  }

  const statusBadge = (status: string) => {
    const variants: Record<string, 'success' | 'warning' | 'secondary' | 'default'> = {
      submitted: 'success',
      prepared: 'warning',
      draft: 'secondary',
      cancelled: 'default',
    }
    return <Badge variant={variants[status] || 'secondary'}>{status}</Badge>
  }

  const columns: Column<Application>[] = [
    { key: 'job', header: 'Job', cell: (app) => (
      <div>
        <Link to={`/jobs/${app.job_id}`} className="text-sm font-medium hover:text-primary">
          {app.job_title || app.job_id}
        </Link>
        {app.company_name && <p className="text-xs text-muted-foreground">{app.company_name}</p>}
      </div>
    )},
    { key: 'status', header: 'Status', cell: (app) => statusBadge(app.status) },
    { key: 'created', header: 'Created', cell: (app) => <span className="text-sm text-muted-foreground">{new Date(app.created_at).toLocaleDateString()}</span> },
    { key: 'submitted', header: 'Submitted', cell: (app) => <span className="text-sm text-muted-foreground">{app.submitted_at ? new Date(app.submitted_at).toLocaleDateString() : '-'}</span> },
    { key: 'actions', header: 'Actions', className: 'text-right', cell: (app) => (
      <div className="flex justify-end gap-1">
        {app.status === 'prepared' && (
          <Button variant="ghost" size="sm" onClick={() => handleSubmit(app.id)} title="Submit">
            <Send className="h-4 w-4" />
          </Button>
        )}
        {['prepared', 'draft'].includes(app.status) && (
          <Button variant="ghost" size="sm" onClick={() => handleCancel(app.id)} title="Cancel">
            <XCircle className="h-4 w-4" />
          </Button>
        )}
        <Link to={`/applications/${app.id}`}>
          <Button variant="ghost" size="sm">
            <ExternalLink className="h-4 w-4" />
          </Button>
        </Link>
      </div>
    )},
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Applications"
        description="Track and manage your job applications."
        actions={
          <div className="flex gap-2">
            {['', 'prepared', 'submitted', 'draft', 'cancelled'].map(s => (
              <Button key={s} variant={statusFilter === s ? 'default' : 'outline'} size="sm" onClick={() => { setStatusFilter(s); setPage(1) }}>
                {s || 'All'}
              </Button>
            ))}
          </div>
        }
      />

      {!isLoading && items.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No applications yet"
          description="Prepare applications for jobs you're interested in."
          action={<Link to="/jobs"><Button>Browse Jobs</Button></Link>}
        />
      ) : (
        <DataTable
          columns={columns}
          data={items}
          loading={isLoading}
          page={(data as any)?.page || page}
          totalPages={(data as any)?.total_pages || 1}
          total={(data as any)?.total}
          onPageChange={setPage}
        />
      )}
    </div>
  )
}
