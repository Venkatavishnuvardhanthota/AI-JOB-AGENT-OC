import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { ResumePerformance as RP } from '@/services/analytics'
import { Award, TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface ResumePerformanceProps {
  title: string
  data: RP[]
  loading: boolean
}

export function ResumePerformance({ title, data, loading }: ResumePerformanceProps) {
  if (loading) {
    return <Card><CardContent className="p-6"><div className="h-48 bg-dark-700 rounded animate-pulse" /></CardContent></Card>
  }

  if (data.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle>{title}</CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-6">No data available. Start applying with different resume versions to compare.</p>
        </CardContent>
      </Card>
    )
  }

  const maxApps = Math.max(...data.map(d => d.applications), 1)
  const bestOverall = data.sort((a, b) => b.offerRate - a.offerRate)[0]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {title}
          {data.length > 1 && (
            <Badge variant="secondary" className="text-xs">{data.length} versions</Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {data.map((item) => {
          const barWidth = Math.round((item.applications / maxApps) * 100)
          const isBest = item.resumeId === bestOverall.resumeId
          return (
            <div key={item.resumeId}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{item.version}</span>
                  {isBest && data.length > 1 && <Award className="h-4 w-4 text-amber-400" />}
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>{item.applications} apps</span>
                  <span className="text-muted-foreground/40">|</span>
                  <span>{item.interviews} int</span>
                  <span className="text-muted-foreground/40">|</span>
                  <span className="text-green-400">{item.offers} off</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex-1 h-6 rounded bg-dark-700 overflow-hidden">
                  <div className="h-full rounded bg-primary/40 transition-all duration-500" style={{ width: `${barWidth}%` }} />
                </div>
                <div className="w-16 text-right shrink-0">
                  <div className="flex items-center gap-1 justify-end">
                    {item.interviewRate > 30 ? <TrendingUp className="h-3 w-3 text-green-400" /> : item.interviewRate > 10 ? <Minus className="h-3 w-3 text-muted-foreground" /> : <TrendingDown className="h-3 w-3 text-warning" />}
                    <span className="text-xs">{item.interviewRate}% int</span>
                  </div>
                  <span className="text-[10px] text-muted-foreground">{item.offerRate}% offer</span>
                </div>
              </div>
            </div>
          )
        })}

        {data.length >= 2 && (
          <div className="border-t border-glass-border pt-3 mt-3">
            <p className="text-xs text-muted-foreground">
              <span className="text-green-400 font-medium">{bestOverall.version}</span> has the highest offer rate at {bestOverall.offerRate}%.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
