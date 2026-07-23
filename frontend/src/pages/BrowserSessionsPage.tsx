import { useState } from 'react'
import { PageHeader } from '@/components/layout/page-header'
import { DataTable, type Column } from '@/components/layout/data-table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Globe, Play, StopCircle, RefreshCw } from 'lucide-react'
import { formatDate } from '@/lib/utils'

interface BrowserSession {
  id: string
  name: string
  status: string
  browser: string
  started_at: string
  pages_visited: number
}

const mockData: BrowserSession[] = [
  { id: '1', name: 'LinkedIn Scraper', status: 'running', browser: 'Chromium', started_at: new Date().toISOString(), pages_visited: 42 },
  { id: '2', name: 'Indeed Parser', status: 'idle', browser: 'Chromium', started_at: new Date(Date.now() - 3600000).toISOString(), pages_visited: 150 },
  { id: '3', name: 'Glassdoor Collector', status: 'crashed', browser: 'Firefox', started_at: new Date(Date.now() - 7200000).toISOString(), pages_visited: 23 },
  { id: '4', name: 'Company Research', status: 'running', browser: 'Chromium', started_at: new Date(Date.now() - 1800000).toISOString(), pages_visited: 8 },
]

export function BrowserSessionsPage() {
  const [page, setPage] = useState(1)

  const statusBadge = (status: string) => {
    const variants: Record<string, 'success' | 'secondary' | 'warning' | 'destructive'> = {
      running: 'success', idle: 'secondary', crashed: 'destructive',
    }
    return <Badge variant={variants[status] || 'secondary'}>{status}</Badge>
  }

  const columns: Column<BrowserSession>[] = [
    { key: 'name', header: 'Session', cell: (s) => (
      <div>
        <span className="text-sm font-medium">{s.name}</span>
        <p className="text-xs text-muted-foreground">{s.browser}</p>
      </div>
    )},
    { key: 'status', header: 'Status', cell: (s) => statusBadge(s.status) },
    { key: 'pages', header: 'Pages Visited', cell: (s) => <span className="text-sm">{s.pages_visited}</span> },
    { key: 'started', header: 'Started', cell: (s) => <span className="text-sm text-muted-foreground">{formatDate(s.started_at)}</span> },
    { key: 'actions', header: '', className: 'text-right', cell: () => (
      <div className="flex justify-end gap-1">
        <Button variant="ghost" size="sm"><Play className="h-4 w-4" /></Button>
        <Button variant="ghost" size="sm"><StopCircle className="h-4 w-4" /></Button>
        <Button variant="ghost" size="sm"><RefreshCw className="h-4 w-4" /></Button>
      </div>
    )},
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Browser Sessions"
        description="Manage browser automation sessions."
        actions={<Button><Globe className="h-4 w-4 mr-1" /> New Session</Button>}
      />
      <DataTable columns={columns} data={mockData} page={page} totalPages={1} onPageChange={setPage} />
    </div>
  )
}
