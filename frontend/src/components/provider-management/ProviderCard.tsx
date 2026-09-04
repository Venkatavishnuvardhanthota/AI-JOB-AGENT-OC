import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Activity, Clock, Star, Shield, MapPin } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ManagedProvider } from '@/services/provider-management'

const STATUS_COLORS: Record<string, string> = {
  healthy: 'text-success bg-success/10 border-success/20',
  degraded: 'text-warning bg-warning/10 border-warning/20',
  unhealthy: 'text-error bg-error/10 border-error/20',
  disabled: 'text-muted-foreground bg-dark-800 border-glass-border',
}

const BACKEND_STATE_COLORS: Record<string, string> = {
  ready: 'text-success bg-success/10 border-success/20',
  disabled: 'text-muted-foreground bg-dark-800 border-glass-border',
  unavailable: 'text-warning bg-warning/10 border-warning/20',
  not_implemented: 'text-error bg-error/10 border-error/20',
  initialization_failed: 'text-error bg-error/10 border-error/20',
  unknown: 'text-muted-foreground bg-dark-800 border-glass-border',
}

interface ProviderCardProps {
  provider: ManagedProvider
  onToggle: (id: string, enabled: boolean) => void
  onClick: (id: string) => void
}

export function ProviderCard({ provider, onToggle, onClick }: ProviderCardProps) {
  return (
    <Card
      className={cn(
        'cursor-pointer transition-all hover:border-primary/30 hover:shadow-sm',
        !provider.enabled && 'opacity-60'
      )}
      onClick={() => onClick(provider.id)}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-semibold text-sm truncate">{provider.name}</h3>
              <Badge variant="outline" className="text-[10px] px-1.5 py-0 shrink-0">
                v{provider.version}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">{provider.category}</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-1.5 mb-3">
          <Badge
            variant="outline"
            className={cn('text-[10px] px-1.5 py-0 border', STATUS_COLORS[provider.health.status] ?? STATUS_COLORS.healthy)}
          >
            <Activity className="h-2.5 w-2.5 mr-1" />
            {provider.health.status}
          </Badge>
          {provider.backendState && (
            <Badge
              variant="outline"
              className={cn('text-[10px] px-1.5 py-0 border', BACKEND_STATE_COLORS[provider.backendState] ?? BACKEND_STATE_COLORS.unknown)}
              title={`Backend: ${provider.backendState}`}
            >
              {provider.backendState.replace(/_/g, ' ')}
            </Badge>
          )}
          <Badge variant="outline" className="text-[10px] px-1.5 py-0">
            <Shield className="h-2.5 w-2.5 mr-1" />
            P{provider.priority}
          </Badge>
          <Badge variant="outline" className="text-[10px] px-1.5 py-0">
            <MapPin className="h-2.5 w-2.5 mr-1" />
            {provider.metadata.region[0] ?? 'global'}
          </Badge>
        </div>

        <div className="grid grid-cols-2 gap-2 text-[11px] text-muted-foreground">
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            <span>{provider.health.averageLatency > 0 ? `${provider.health.averageLatency}ms` : '-'}</span>
          </div>
          <div className="flex items-center gap-1">
            <Star className="h-3 w-3" />
            <span>{Math.round(provider.metadata.reliabilityScore * 100)}%</span>
          </div>
        </div>

        <div className="flex gap-1 mt-2">
          <Button
            variant={provider.enabled ? 'destructive' : 'default'}
            size="sm"
            className="h-6 text-[10px] px-2"
            onClick={(e) => { e.stopPropagation(); onToggle(provider.id, !provider.enabled) }}
          >
            {provider.enabled ? 'Disable' : 'Enable'}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
