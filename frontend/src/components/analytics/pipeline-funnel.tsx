import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { getStatusLabel } from '@/services/status'
import { cn } from '@/lib/utils'
import type { FunnelMetrics } from '@/services/analytics'
import { APPLICATION_STATUSES } from '@/services/status'
import { AlertTriangle, ArrowRight, TrendingDown } from 'lucide-react'

interface PipelineFunnelProps {
  funnel: FunnelMetrics | null
  loading: boolean
}

export function PipelineFunnel({ funnel, loading }: PipelineFunnelProps) {
  if (loading || !funnel) {
    return <Card><CardContent className="p-6"><div className="h-64 bg-dark-700 rounded animate-pulse" /></CardContent></Card>
  }

  const maxCount = Math.max(...funnel.stages.map(s => s.count), 1)

  const groupedStages = APPLICATION_STATUSES.map(status => {
    const stage = funnel.stages.find(s => s.status === status)
    return stage || { status, label: getStatusLabel(status), count: 0, category: '' }
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Pipeline Funnel
          {funnel.bottlenecks.length > 0 && (
            <Badge variant="warning" className="text-xs">{funnel.bottlenecks.length} issues</Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {groupedStages.map((stage, i) => {
            const pct = maxCount > 0 ? Math.round((stage.count / maxCount) * 100) : 0
            const prevStage = i > 0 ? groupedStages[i - 1] : null
            const conversion = prevStage && prevStage.count > 0 ? Math.round((stage.count / prevStage.count) * 100) : null
            const bottleneck = funnel.bottlenecks.find(b => {
              const stageLabel = getStatusLabel(stage.status).toLowerCase()
              return b.stage.toLowerCase() === stageLabel
            })

            return (
              <div key={stage.status}>
                <div className="flex items-center gap-3">
                  <div className="w-24 shrink-0">
                    <p className="text-xs font-medium truncate" title={stage.label}>{stage.label}</p>
                  </div>
                  <div className="flex-1">
                    <div className="relative h-8 rounded-md bg-dark-700 overflow-hidden">
                      <div
                        className={cn(
                          'h-full rounded-md transition-all duration-500',
                          stage.category === 'preparation' && 'bg-blue-500/30',
                          stage.category === 'active' && 'bg-green-500/30',
                          stage.category === 'interview' && 'bg-purple-500/30',
                          stage.category === 'offer' && 'bg-amber-500/30',
                          stage.category === 'final' && 'bg-emerald-500/30',
                        )}
                        style={{ width: `${Math.max(pct, 2)}%` }}
                      />
                      <div className="absolute inset-0 flex items-center px-2">
                        <div className="flex items-center justify-between w-full">
                          <span className="text-xs font-medium">{stage.count}</span>
                          {conversion !== null && (
                            <span className="text-[10px] text-muted-foreground">{conversion}%</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="w-12 text-right shrink-0">
                    <span className="text-xs text-muted-foreground">{pct}%</span>
                  </div>
                </div>
                {conversion !== null && conversion < 50 && i > 0 && prevStage && prevStage.count > 0 && (
                  <div className="flex items-center gap-1 ml-28 mb-1">
                    <TrendingDown className="h-3 w-3 text-warning" />
                    <span className="text-[10px] text-warning">{100 - conversion}% drop-off</span>
                  </div>
                )}
                {bottleneck && (
                  <div className="flex items-center gap-1 ml-28 mb-1">
                    <AlertTriangle className="h-3 w-3 text-warning" />
                    <span className="text-[10px] text-warning">{bottleneck.message}</span>
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {funnel.conversionRates.length > 0 && (
          <div className="mt-6">
            <h4 className="text-sm font-medium mb-2">Stage Transition Rates</h4>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {funnel.conversionRates.filter(r => r.rate > 0).map(r => (
                <div key={`${r.from}-${r.to}`} className="flex items-center gap-1 text-xs bg-dark-800 rounded px-2 py-1">
                  <span className="truncate">{r.from}</span>
                  <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />
                  <span className="truncate">{r.to}</span>
                  <span className={cn('ml-auto font-medium', r.rate < 30 ? 'text-warning' : 'text-green-400')}>
                    {r.rate}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
