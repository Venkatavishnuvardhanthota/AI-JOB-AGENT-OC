import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { SourceAnalytics as SA } from '@/services/analytics'
import { Globe, TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface SourceAnalyticsProps {
  data: SA[]
  loading: boolean
}

export function SourceAnalytics({ data, loading }: SourceAnalyticsProps) {
  if (loading) {
    return <Card><CardContent className="p-6"><div className="h-48 bg-dark-700 rounded animate-pulse" /></CardContent></Card>
  }

  if (data.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle>Source Analytics</CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-6">No source data available yet.</p>
        </CardContent>
      </Card>
    )
  }

  const sorted = data.sort((a, b) => b.applications - a.applications)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Source Analytics
          <Badge variant="outline" className="text-xs">{data.length} sources</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {sorted.map((source) => {
            const maxApps = Math.max(...sorted.map(s => s.applications), 1)
            const barWidth = Math.round((source.applications / maxApps) * 100)
            return (
              <div key={source.source}>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <Globe className="h-3.5 w-3.5 text-muted-foreground" />
                    <span className="text-sm font-medium">{source.source}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>{source.applications} apps</span>
                    <span>{source.interviews} int</span>
                    <span className="text-green-400">{source.offers} off</span>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex-1 h-6 rounded bg-dark-700 overflow-hidden">
                    <div className="h-full rounded bg-primary/40 transition-all duration-500" style={{ width: `${barWidth}%` }} />
                  </div>
                  <div className="text-right shrink-0 w-16">
                    <div className="flex items-center gap-1 justify-end">
                      {source.interviewRate > 30 ? <TrendingUp className="h-3 w-3 text-green-400" /> : source.interviewRate > 10 ? <Minus className="h-3 w-3 text-muted-foreground" /> : <TrendingDown className="h-3 w-3 text-warning" />}
                      <span className="text-xs">{source.interviewRate}% int</span>
                    </div>
                    <span className="text-[10px] text-muted-foreground">{source.responseRate}% resp</span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
