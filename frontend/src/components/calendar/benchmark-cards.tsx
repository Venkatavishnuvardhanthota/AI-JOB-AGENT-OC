import { useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { computeBenchmarkCards } from '@/services/timeline-intelligence'
import type { Application } from '@/types'
import { TrendingUp, TrendingDown, Minus, BarChart3 } from 'lucide-react'

interface BenchmarkCardsProps {
  applications: Application[]
  loading: boolean
}

export function BenchmarkCards({ applications, loading }: BenchmarkCardsProps) {
  const cards = useMemo(() => computeBenchmarkCards(applications), [applications])

  if (loading) {
    return <Card><CardContent className="p-6"><div className="h-32 bg-dark-700 rounded animate-pulse" /></CardContent></Card>
  }

  const getTrendColor = (trend: string): string => {
    if (trend === 'positive') return 'text-green-400'
    if (trend === 'negative') return 'text-red-400'
    return 'text-muted-foreground'
  }

  const getBorderColor = (trend: string): string => {
    if (trend === 'positive') return 'border-green-500/20'
    if (trend === 'negative') return 'border-red-500/20'
    return 'border-glass-border'
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm">
          <BarChart3 className="h-4 w-4 text-primary" /> Benchmark Cards
          <Badge variant="outline" className="text-[10px]">{cards.length} metrics</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {cards.map((card, i) => (
            <div
              key={i}
              className={cn(
                'rounded-lg border p-3 transition-colors hover:bg-dark-800/50',
                getBorderColor(card.trend),
              )}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-muted-foreground">{card.label}</span>
                {card.trend === 'positive' && <TrendingUp className="h-3.5 w-3.5 text-green-400" />}
                {card.trend === 'negative' && <TrendingDown className="h-3.5 w-3.5 text-red-400" />}
                {card.trend === 'neutral' && <Minus className="h-3.5 w-3.5 text-muted-foreground" />}
              </div>
              <div className="flex items-baseline gap-2">
                <span className={cn('text-lg font-semibold', getTrendColor(card.trend))}>{card.value}</span>
                {card.change !== undefined && (
                  <span className={cn(
                    'text-xs',
                    card.change > 0 ? 'text-green-400' : card.change < 0 ? 'text-red-400' : 'text-muted-foreground',
                  )}>
                    {card.change > 0 ? '+' : ''}{card.change}
                  </span>
                )}
              </div>
              <p className="text-[10px] text-muted-foreground mt-0.5">{card.description}</p>
              {card.previousValue && (
                <p className="text-[9px] text-muted-foreground mt-0.5">Previous: {card.previousValue}</p>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
