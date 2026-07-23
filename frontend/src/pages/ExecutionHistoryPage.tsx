import { useState } from 'react'
import { PageHeader } from '@/components/layout/page-header'
import { DataTable, type Column } from '@/components/layout/data-table'
import { Badge } from '@/components/ui/badge'
import { formatDate } from '@/lib/utils'

interface Execution {
  id: string
  pipeline: string
  status: string
  started_at: string
  completed_at: string | null
  duration: string
  mode: string
}

const mockData: Execution[] = [
  { id: '1', pipeline: 'Daily Job Discovery', status: 'completed', started_at: new Date(Date.now() - 86400000).toISOString(), completed_at: new Date(Date.now() - 85500000).toISOString(), duration: '15m', mode: 'scheduled' },
  { id: '2', pipeline: 'Application Batch #42', status: 'completed', started_at: new Date(Date.now() - 172800000).toISOString(), completed_at: new Date(Date.now() - 171000000).toISOString(), duration: '30m', mode: 'manual' },
  { id: '3', pipeline: 'Profile Enrichment', status: 'failed', started_at: new Date(Date.now() - 259200000).toISOString(), completed_at: null, duration: '12m', mode: 'automatic' },
  { id: '4', pipeline: 'Match Scoring', status: 'completed', started_at: new Date(Date.now() - 345600000).toISOString(), completed_at: new Date(Date.now() - 344400000).toISOString(), duration: '20m', mode: 'manual' },
  { id: '5', pipeline: 'Daily Job Discovery', status: 'completed', started_at: new Date(Date.now() - 432000000).toISOString(), completed_at: new Date(Date.now() - 431100000).toISOString(), duration: '15m', mode: 'scheduled' },
]

export function ExecutionHistoryPage() {
  const [page, setPage] = useState(1)

  const statusBadge = (status: string) => {
    const variants: Record<string, 'success' | 'warning' | 'destructive'> = {
      completed: 'success', failed: 'destructive', running: 'warning',
    }
    return <Badge variant={variants[status] || 'secondary'}>{status}</Badge>
  }

  const columns: Column<Execution>[] = [
    { key: 'pipeline', header: 'Pipeline', cell: (e) => <span className="text-sm font-medium">{e.pipeline}</span> },
    { key: 'status', header: 'Status', cell: (e) => statusBadge(e.status) },
    { key: 'mode', header: 'Mode', cell: (e) => <Badge variant="outline">{e.mode}</Badge> },
    { key: 'started', header: 'Started', cell: (e) => <span className="text-sm text-muted-foreground">{formatDate(e.started_at)}</span> },
    { key: 'duration', header: 'Duration', cell: (e) => <span className="text-sm text-muted-foreground">{e.duration}</span> },
  ]

  return (
    <div className="space-y-6">
      <PageHeader title="Execution History" description="History of pipeline executions." />
      <DataTable columns={columns} data={mockData} page={page} totalPages={1} onPageChange={setPage} />
    </div>
  )
}