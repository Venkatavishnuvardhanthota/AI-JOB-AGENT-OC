import { useEffect, useState } from 'react'
import { Card } from '@/components/ui/card'
import { metricsService } from '@/services/production/metrics-service'
import { performanceService } from '@/services/production/performance-service'
import { Activity, Clock, BarChart3, TrendingUp, Zap, Target } from 'lucide-react'

export function MetricsPanel() {
  const [metrics, setMetrics] = useState<{ name: string; current: number; unit: string; avg: number; min: number; max: number }[]>([])
  const [perfSummary, setPerfSummary] = useState(performanceService.getPerformanceSummary())

  const refresh = () => {
    setMetrics(metricsService.getMetricsSummary())
    setPerfSummary(performanceService.getPerformanceSummary())
  }
  useEffect(() => { refresh(); const iv = setInterval(refresh, 15000); return () => clearInterval(iv) }, [])

  const metricCards = [
    { label: 'Total Operations', value: perfSummary.totalOperations, unit: 'ops', icon: Activity, color: 'text-blue-400' },
    { label: 'Avg Duration', value: `${perfSummary.avgDuration}ms`, unit: '', icon: Clock, color: 'text-purple-400' },
    { label: 'Slow Ops', value: perfSummary.slowOperations, unit: 'ops', icon: Zap, color: 'text-yellow-400' },
    { label: 'Failure Rate', value: `${perfSummary.failureRate}%`, unit: '', icon: Target, color: perfSummary.failureRate > 10 ? 'text-red-400' : 'text-green-400' },
    { label: 'Active Metrics', value: metrics.length, unit: 'series', icon: BarChart3, color: 'text-cyan-400' },
    { label: 'Avg Throughput', value: metrics.filter(m => m.unit === 'count').reduce((s, m) => s + m.current, 0), unit: 'ops', icon: TrendingUp, color: 'text-emerald-400' },
  ]

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium">Performance Metrics</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
        {metricCards.map(mc => {
          const Icon = mc.icon
          return (
            <Card key={mc.label} className="p-2 space-y-1">
              <div className="flex items-center gap-1">
                <Icon className={`h-3 w-3 ${mc.color}`} />
                <span className="text-[10px] text-muted-foreground">{mc.label}</span>
              </div>
              <p className="text-lg font-bold">{mc.value}</p>
              {mc.unit && <p className="text-[10px] text-muted-foreground">{mc.unit}</p>}
            </Card>
          )
        })}
      </div>

      {metrics.length > 0 && (
        <>
          <h4 className="text-xs font-medium text-muted-foreground">Metric Series</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
            {metrics.slice(0, 20).map(m => (
              <Card key={m.name} className="p-2">
                <p className="text-[10px] text-muted-foreground truncate">{m.name}</p>
                <p className="text-sm font-bold">{m.current} <span className="text-[10px] font-normal text-muted-foreground">{m.unit}</span></p>
                <div className="flex gap-2 text-[10px] text-muted-foreground">
                  <span>avg {m.avg}</span>
                  <span>min {m.min}</span>
                  <span>max {m.max}</span>
                </div>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
