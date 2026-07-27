import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { Insight } from '@/services/analytics'
import { Lightbulb, TrendingUp, TrendingDown, Info } from 'lucide-react'

interface InsightCardsProps {
  insights: Insight[]
  loading: boolean
}

export function InsightCards({ insights, loading }: InsightCardsProps) {
  if (loading) {
    return <Card><CardContent className="p-6"><div className="h-32 bg-dark-700 rounded animate-pulse" /></CardContent></Card>
  }

  if (insights.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-6 text-muted-foreground">
            <Lightbulb className="h-8 w-8 mb-2 opacity-40" />
            <p className="text-sm">Apply to more jobs to generate insights.</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Insights
          <Badge variant="outline" className="text-xs">{insights.length} insights</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {insights.map(insight => (
          <div
            key={insight.id}
            className={cn(
              'flex items-start gap-3 rounded-lg border p-3 transition-colors',
              insight.type === 'positive' && 'border-green-500/20 bg-green-500/5',
              insight.type === 'negative' && 'border-red-500/20 bg-red-500/5',
              insight.type === 'info' && 'border-blue-500/20 bg-blue-500/5',
            )}
          >
            <div className="mt-0.5">
              {insight.type === 'positive' && <TrendingUp className="h-4 w-4 text-green-400" />}
              {insight.type === 'negative' && <TrendingDown className="h-4 w-4 text-red-400" />}
              {insight.type === 'info' && <Info className="h-4 w-4 text-blue-400" />}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <p className="text-sm font-medium">{insight.title}</p>
                {insight.metric && (
                  <Badge variant="outline" className="text-[10px]">{insight.metric}</Badge>
                )}
              </div>
              <p className="text-xs text-muted-foreground">{insight.description}</p>
              {insight.change !== undefined && (
                <span className={cn('text-xs font-medium', insight.change > 0 ? 'text-green-400' : 'text-red-400')}>
                  {insight.change > 0 ? '+' : ''}{insight.change}%
                </span>
              )}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
