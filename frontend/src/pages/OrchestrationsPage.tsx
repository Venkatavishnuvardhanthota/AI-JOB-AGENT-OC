import { useState } from 'react'
import { PageHeader } from '@/components/layout/page-header'
import { DataTable, type Column } from '@/components/layout/data-table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Play, RotateCcw } from 'lucide-react'
import { formatDate } from '@/lib/utils'

interface Orchestration {
  id: string
  name: string
  status: string
  mode: string
  started_at: string
  completed_at: string | null
  progress: number
}

const mockData: Orchestration[] = [
  { id: '1', name: 'Daily Job Discovery', status: 'running', mode: 'scheduled', started_at: new Date().toISOString(), completed_at: null, progress: 65 },
  { id: '2', name: 'Application Batch #42', status: 'completed', mode: 'manual', started_at: new Date(Date.now() - 3600000).toISOString(), completed_at: new Date().toISOString(), progress: 100 },
  { id: '3', name: 'Profile Enrichment', status: 'paused', mode: 'automatic', started_at: new Date(Date.now() - 7200000).toISOString(), completed_at: null, progress: 45 },
  { id: '4', name: 'Match Scoring Pipeline', status: 'failed', mode: 'manual', started_at: new Date(Date.now() - 14400000).toISOString(), completed_at: new Date(Date.now() - 10800000).toISOString(), progress: 30 },
]

export function OrchestrationsPage() {
  const [page, setPage] = useState(1)

  const statusBadge = (status: string) => {
    const variants: Record<string, 'success' | 'warning' | 'default' | 'destructive'> = {
      running: 'default', completed: 'success', paused: 'warning', failed: 'destructive',
    }
    return <Badge variant={variants[status] || 'secondary'}>{status}</Badge>
  }

  const columns: Column<Orchestration>[] = [
    { key: 'name', header: 'Name', cell: (o) => <span className="text-sm font-medium">{o.name}</span> },
    { key: 'status', header: 'Status', cell: (o) => statusBadge(o.status) },
    { key: 'mode', header: 'Mode', cell: (o) => <Badge variant="outline">{o.mode}</Badge> },
    { key: 'started', header: 'Started', cell: (o) => <span className="text-sm text-muted-foreground">{formatDate(o.started_at)}</span> },
    { key: 'progress', header: 'Progress', cell: (o) => (
      <div className="flex items-center gap-2">
        <div className="h-2 flex-1 rounded-full bg-dark-800 overflow-hidden max-w-24">
          <div className={`h-full rounded-full ${o.status === 'completed' ? 'bg-success' : o.status === 'running' ? 'bg-primary' : o.status === 'failed' ? 'bg-error' : 'bg-warning'}`} style={{ width: `${o.progress}%` }} />
        </div>
        <span className="text-xs text-muted-foreground">{o.progress}%</span>
      </div>
    )},
    { key: 'actions', header: '', className: 'text-right', cell: () => (
      <div className="flex justify-end gap-1">
        <Button variant="ghost" size="sm"><Play className="h-4 w-4" /></Button>
        <Button variant="ghost" size="sm"><RotateCcw className="h-4 w-4" /></Button>
      </div>
    )},
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Orchestrations"
        description="Pipeline execution management."
        actions={<Button><Play className="h-4 w-4 mr-1" /> New Orchestration</Button>}
      />
      <DataTable columns={columns} data={mockData} page={page} totalPages={1} onPageChange={setPage} />
    </div>
  )
}
