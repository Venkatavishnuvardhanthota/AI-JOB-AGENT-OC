import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useAIHealth } from '@/api/hooks'
import {
  Activity,
  HeartPulse,
  Wifi,
  WifiOff,
  Clock,
  XCircle,
  RefreshCw,
} from 'lucide-react'

export function HealthOverview() {
  const { data: health, isLoading, isError, refetch, isRefetching } = useAIHealth()

  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><Activity className="h-5 w-5 text-primary" />Live Status</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          {[1, 2, 3].map(i => <Skeleton key={i} className="h-12 w-full" />)}
        </CardContent>
      </Card>
    )
  }

  if (isError) {
    return (
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><Activity className="h-5 w-5 text-primary" />Live Status</CardTitle></CardHeader>
        <CardContent>
          <div className="text-center py-4">
            <p className="text-sm text-error">Failed to load health status</p>
            <button onClick={() => refetch()} className="text-xs text-primary hover:underline mt-1">Retry</button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" />
            Live Status
          </span>
          <div className="flex items-center gap-2">
            <Badge variant={health?.overall_healthy ? 'success' : 'destructive'}>
              {health?.overall_healthy ? 'All Healthy' : 'Degraded'}
            </Badge>
            <button onClick={() => refetch()} disabled={isRefetching} className="text-muted-foreground hover:text-foreground">
              <RefreshCw className={`h-3 w-3 ${isRefetching ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {health?.providers?.map(p => (
          <div
            key={p.provider}
            className="flex items-center justify-between rounded-lg border border-glass-border p-3 text-sm"
          >
            <div className="flex items-center gap-3">
              <div className={`p-1.5 rounded-full ${p.healthy ? 'bg-success/10' : 'bg-error/10'}`}>
                {p.healthy
                  ? <HeartPulse className="h-4 w-4 text-success" />
                  : <XCircle className="h-4 w-4 text-error" />
                }
              </div>
              <div>
                <p className="font-medium">{p.provider}</p>
                {p.model && <p className="text-xs text-muted-foreground">Model: {p.model}</p>}
              </div>
            </div>
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                {p.connected ? <Wifi className="h-3 w-3 text-success" /> : <WifiOff className="h-3 w-3 text-error" />}
                {p.connected ? 'Connected' : 'Disconnected'}
              </span>
              {p.latency_ms != null && (
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {p.latency_ms.toFixed(0)}ms
                </span>
              )}
              {p.is_default && <Badge variant="default" className="text-[10px]">Default</Badge>}
            </div>
            {p.error && <p className="text-xs text-error mt-1 col-span-2">{p.error}</p>}
          </div>
        ))}
        {(!health?.providers || health.providers.length === 0) && (
          <p className="text-sm text-muted-foreground text-center py-4">No provider health data available</p>
        )}
        <p className="text-[10px] text-muted-foreground text-right">
          Last updated: {new Date().toLocaleTimeString()}
        </p>
      </CardContent>
    </Card>
  )
}
