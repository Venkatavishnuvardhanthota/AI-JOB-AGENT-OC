import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { Application } from '@/types'
import {
  computeBenchmarkCards,
  computeAverageResponseTime,
  computeAverageHiringDuration,
  computeFastestHiringProcess,
  computeSlowestHiringProcess,
  computeMedianHiringDuration,
} from '@/services/timeline-intelligence'
import { TrendingUp, TrendingDown, Minus, Clock, Zap, Hourglass, Target } from 'lucide-react'

interface TimelineIntelligenceProps {
  applications: Application[]
  loading: boolean
}

export function TimelineIntelligence({ applications, loading }: TimelineIntelligenceProps) {
  if (loading) {
    return <Card><CardContent className="p-6"><div className="h-48 bg-dark-700 rounded animate-pulse" /></CardContent></Card>
  }

  const benchmarkCards = computeBenchmarkCards(applications)
  const avgResponseDays = computeAverageResponseTime(applications)
  const avgHiringDays = computeAverageHiringDuration(applications)
  const medianDays = computeMedianHiringDuration(applications)
  const fastest = computeFastestHiringProcess(applications)
  const slowest = computeSlowestHiringProcess(applications)

  const hiredCount = applications.filter(a => a.status === 'accepted').length

  const trendIcon = (trend: string) => {
    if (trend === 'positive') return <TrendingUp className="h-3.5 w-3.5 text-green-400" />
    if (trend === 'negative') return <TrendingDown className="h-3.5 w-3.5 text-red-400" />
    return <Minus className="h-3.5 w-3.5 text-muted-foreground" />
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm">
          Timeline Intelligence
          {hiredCount > 0 && <Badge variant="outline" className="text-[10px]">{hiredCount} offers accepted</Badge>}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="rounded-lg border border-glass-border bg-dark-800 p-3">
            <div className="flex items-center gap-1 text-xs text-muted-foreground mb-1">
              <Clock className="h-3 w-3" /> Avg Response Time
            </div>
            <p className="text-xl font-semibold">{avgResponseDays > 0 ? `${avgResponseDays} days` : 'N/A'}</p>
          </div>
          <div className="rounded-lg border border-glass-border bg-dark-800 p-3">
            <div className="flex items-center gap-1 text-xs text-muted-foreground mb-1">
              <Hourglass className="h-3 w-3" /> Avg Hiring Duration
            </div>
            <p className="text-xl font-semibold">{avgHiringDays > 0 ? `${avgHiringDays} days` : 'N/A'}</p>
          </div>
          <div className="rounded-lg border border-glass-border bg-dark-800 p-3">
            <div className="flex items-center gap-1 text-xs text-muted-foreground mb-1">
              <Target className="h-3 w-3" /> Median Hiring
            </div>
            <p className="text-xl font-semibold">{medianDays > 0 ? `${medianDays} days` : 'N/A'}</p>
          </div>
          {fastest && (
            <div className="rounded-lg border border-green-500/20 bg-green-500/5 p-3">
              <div className="flex items-center gap-1 text-xs text-green-400 mb-1">
                <Zap className="h-3 w-3" /> Fastest Process
              </div>
              <p className="text-sm font-semibold">{fastest.company}</p>
              <p className="text-xs text-muted-foreground">{fastest.days} days</p>
            </div>
          )}
          {slowest && (
            <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-3">
              <div className="flex items-center gap-1 text-xs text-red-400 mb-1">
                <Hourglass className="h-3 w-3" /> Slowest Process
              </div>
              <p className="text-sm font-semibold">{slowest.company}</p>
              <p className="text-xs text-muted-foreground">{slowest.days} days</p>
            </div>
          )}
        </div>

        <div className="space-y-2">
          <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Benchmark Cards</h4>
          {benchmarkCards.map((card, i) => (
            <div key={i} className={cn(
              'flex items-center gap-3 rounded-lg border p-3',
              card.trend === 'positive' && 'border-green-500/20',
              card.trend === 'negative' && 'border-red-500/20',
              card.trend === 'neutral' && 'border-glass-border',
            )}>
              {trendIcon(card.trend)}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium">{card.label}</p>
                  <span className="text-sm font-semibold">{card.value}</span>
                  {card.change !== undefined && (
                    <span className={cn(
                      'text-xs',
                      card.change > 0 ? 'text-green-400' : card.change < 0 ? 'text-red-400' : 'text-muted-foreground',
                    )}>
                      {card.change > 0 ? '+' : ''}{card.change}
                    </span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">{card.description}</p>
                {card.previousValue && (
                  <p className="text-[10px] text-muted-foreground">Previous: {card.previousValue}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
