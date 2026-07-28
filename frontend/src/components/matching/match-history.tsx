import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Clock, BarChart3 } from 'lucide-react'
import { getDecisionLabel, getDecisionColor } from '@/services/matching'
import type { MatchHistoryEntry } from '@/services/matching'

interface MatchHistoryProps {
  entries: MatchHistoryEntry[]
}

export function MatchHistory({ entries }: MatchHistoryProps) {
  if (entries.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle className="text-sm flex items-center gap-2"><Clock className="w-4 h-4" />Match History</CardTitle></CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground">No matches scored yet. Score jobs to see history.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm flex items-center gap-2">
          <BarChart3 className="w-4 h-4" />
          Match History
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-1.5 max-h-72 overflow-y-auto">
          {entries.slice(0, 15).map(entry => (
            <div key={entry.id} className="flex items-center justify-between p-1.5 rounded hover:bg-dark-800 transition-colors">
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium truncate">{entry.jobTitle}</p>
                <p className="text-[10px] text-muted-foreground truncate">{entry.company}</p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-xs font-bold">{Math.round(entry.overall * 100)}%</span>
                <Badge className={`text-[10px] ${getDecisionColor(entry.decision)}`}>
                  {getDecisionLabel(entry.decision)}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
