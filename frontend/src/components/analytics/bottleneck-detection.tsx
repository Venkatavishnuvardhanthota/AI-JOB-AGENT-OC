import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, AlertCircle, AlertOctagon, Lightbulb } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Bottleneck } from '@/services/analytics'

interface BottleneckDetectionProps {
  bottlenecks: Bottleneck[]
  loading: boolean
}

export function BottleneckDetection({ bottlenecks, loading }: BottleneckDetectionProps) {
  if (loading) {
    return <Card><CardContent className="p-6"><div className="h-32 bg-dark-700 rounded animate-pulse" /></CardContent></Card>
  }

  if (bottlenecks.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">Bottleneck Detection</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-6 text-muted-foreground">
            <AlertCircle className="h-8 w-8 mb-2 opacity-40" />
            <p className="text-sm">No bottlenecks detected. Your pipeline is healthy.</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Bottleneck Detection
          <Badge variant={bottlenecks.some(b => b.severity === 'critical') ? 'destructive' : 'warning'}>
            {bottlenecks.length} issue{bottlenecks.length > 1 ? 's' : ''}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {bottlenecks.map((b, i) => (
          <div key={i} className={cn(
            'rounded-lg border p-3',
            b.severity === 'critical' && 'border-error/30 bg-error/5',
            b.severity === 'warning' && 'border-warning/30 bg-warning/5',
            b.severity === 'info' && 'border-info/30 bg-info/5',
          )}>
            <div className="flex items-start gap-3">
              <div className="mt-0.5">
                {b.severity === 'critical' && <AlertOctagon className="h-4 w-4 text-error" />}
                {b.severity === 'warning' && <AlertTriangle className="h-4 w-4 text-warning" />}
                {b.severity === 'info' && <AlertCircle className="h-4 w-4 text-info" />}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <p className="text-sm font-medium">{b.stage}</p>
                  <Badge variant="outline" className="text-[10px]">{b.count}</Badge>
                  <Badge variant={b.severity === 'critical' ? 'destructive' : b.severity === 'warning' ? 'warning' : 'secondary'} className="text-[10px]">
                    {b.severity}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground">{b.message}</p>
                <div className="flex items-center gap-1 mt-1 text-xs text-primary">
                  <Lightbulb className="h-3 w-3" />
                  <span>{b.suggestion}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
