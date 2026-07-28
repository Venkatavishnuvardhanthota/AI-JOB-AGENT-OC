import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { ProviderHealth, ProviderId } from '@/services/discovery'

interface ProviderStatusProps {
  health: Record<ProviderId, ProviderHealth>
}

const STATUS_COLORS: Record<string, string> = {
  healthy: 'bg-green-500',
  degraded: 'bg-yellow-500',
  unhealthy: 'bg-red-500',
  disabled: 'bg-gray-500',
}

export function ProviderStatus({ health }: ProviderStatusProps) {
  const entries = Object.entries(health)
  if (entries.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle className="text-lg">Provider Status</CardTitle></CardHeader>
        <CardContent><p className="text-sm text-muted-foreground">No provider data available.</p></CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Provider Status</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {entries.map(([id, h]) => (
            <div key={id} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${STATUS_COLORS[h.status] || 'bg-gray-500'}`} />
                <span className="text-sm font-medium capitalize">{id.replace(/_/g, ' ')}</span>
              </div>
              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                <span>{Math.round(h.successRate * 100)}%</span>
                <span>{h.averageLatency}ms</span>
                <Badge variant={h.status === 'healthy' ? 'default' : h.status === 'degraded' ? 'secondary' : 'destructive'} className="text-[10px] px-1.5 py-0">
                  {h.status}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
