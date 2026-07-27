import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Clock, Search, AlertCircle } from 'lucide-react'
import type { DiscoveryHistoryEntry } from '@/services/discovery'

interface DiscoveryHistoryPanelProps {
  entries: DiscoveryHistoryEntry[]
}

export function DiscoveryHistoryPanel({ entries }: DiscoveryHistoryPanelProps) {
  if (entries.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle className="text-lg flex items-center gap-2"><Clock className="w-5 h-5" />Discovery History</CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No searches yet. Run your first search to see history.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Clock className="w-5 h-5" />
          Discovery History
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 max-h-80 overflow-y-auto">
          {entries.slice(0, 20).map(entry => (
            <div key={entry.id} className="flex items-center justify-between p-2 rounded-lg hover:bg-dark-800 transition-colors">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <Search className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                  <p className="text-sm font-medium truncate">{entry.query}</p>
                  {entry.location && <span className="text-xs text-muted-foreground truncate">{entry.location}</span>}
                </div>
                <div className="flex items-center gap-3 mt-0.5 text-[10px] text-muted-foreground">
                  <span>{new Date(entry.timestamp).toLocaleString()}</span>
                  <span>{entry.jobsFound} jobs</span>
                  <span>{entry.duplicatesRemoved} dupes</span>
                  <span>{(entry.executionTime / 1000).toFixed(1)}s</span>
                </div>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                {entry.errors.length > 0 && (
                  <AlertCircle className="w-3.5 h-3.5 text-yellow-400" aria-label={`${entry.errors.length} errors`} />
                )}
                <Badge variant={entry.status === 'completed' ? 'default' : 'secondary'} className="text-[10px]">
                  {entry.status}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
