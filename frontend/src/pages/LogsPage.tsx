import { useState } from 'react'
import { PageHeader } from '@/components/layout/page-header'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Search, RefreshCw } from 'lucide-react'

interface LogEntry {
  id: string
  timestamp: string
  level: string
  source: string
  message: string
}

const mockLogs: LogEntry[] = [
  { id: '1', timestamp: '2026-07-23 10:30:15', level: 'INFO', source: 'orchestrator', message: 'Pipeline "Daily Job Discovery" started' },
  { id: '2', timestamp: '2026-07-23 10:30:16', level: 'DEBUG', source: 'provider', message: 'Fetching jobs from LinkedIn (page 1)' },
  { id: '3', timestamp: '2026-07-23 10:30:18', level: 'WARN', source: 'provider', message: 'Rate limit approaching for Workday API' },
  { id: '4', timestamp: '2026-07-23 10:30:20', level: 'ERROR', source: 'ai', message: 'AI service timeout after 30s' },
  { id: '5', timestamp: '2026-07-23 10:30:22', level: 'INFO', source: 'matching', message: 'Scored 15 jobs' },
  { id: '6', timestamp: '2026-07-23 10:30:25', level: 'INFO', source: 'orchestrator', message: 'Pipeline completed successfully' },
  { id: '7', timestamp: '2026-07-23 10:25:00', level: 'INFO', source: 'auth', message: 'User logged in' },
  { id: '8', timestamp: '2026-07-23 10:20:00', level: 'ERROR', source: 'browser', message: 'Browser session crashed: out of memory' },
]

const levelColors: Record<string, string> = {
  ERROR: 'text-error border-error/30 bg-error/10',
  WARN: 'text-warning border-warning/30 bg-warning/10',
  INFO: 'text-primary border-primary/30 bg-primary/10',
  DEBUG: 'text-muted-foreground border-glass-border bg-dark-800/30',
}

export function LogsPage() {
  const [search, setSearch] = useState('')
  const [levelFilter, setLevelFilter] = useState('')

  const filtered = mockLogs.filter(log => {
    if (levelFilter && log.level !== levelFilter) return false
    if (search && !log.message.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  return (
    <div className="space-y-6">
      <PageHeader
        title="Logs"
        description="System logs and events."
        actions={
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-1" /> Refresh
          </Button>
        }
      />

      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search logs..." value={search} onChange={e => setSearch(e.target.value)} className="pl-9" />
        </div>
        <Select value={levelFilter} onChange={e => setLevelFilter(e.target.value)}>
          <option value="">All Levels</option>
          <option value="ERROR">Error</option>
          <option value="WARN">Warning</option>
          <option value="INFO">Info</option>
          <option value="DEBUG">Debug</option>
        </Select>
      </div>

      <Card className="overflow-hidden">
        <div className="divide-y divide-glass-border">
          {filtered.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">No logs match your filters.</div>
          ) : (
            filtered.map(log => (
              <div key={log.id} className="p-3 hover:bg-white/[0.02] text-sm font-mono">
                <div className="flex items-start gap-3">
                  <span className="text-xs text-muted-foreground whitespace-nowrap">{log.timestamp}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded border ${levelColors[log.level] || ''}`}>{log.level}</span>
                  <span className="text-xs text-muted-foreground">[{log.source}]</span>
                  <span className="text-foreground">{log.message}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  )
}