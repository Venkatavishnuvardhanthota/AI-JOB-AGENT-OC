import { useEffect, useState } from 'react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { healthService } from '@/services/production/health-service'
import type { ServiceHealth, HealthStatus } from '@/services/production/production-types'
import { HeartPulse, AlertTriangle, Shield, Wifi, WifiOff } from 'lucide-react'

const statusConfig: Record<HealthStatus, { label: string; variant: string; icon: React.ElementType }> = {
  healthy: { label: 'Healthy', variant: 'success', icon: HeartPulse },
  warning: { label: 'Warning', variant: 'warning', icon: AlertTriangle },
  degraded: { label: 'Degraded', variant: 'warning', icon: AlertTriangle },
  critical: { label: 'Critical', variant: 'destructive', icon: Shield },
  offline: { label: 'Offline', variant: 'secondary', icon: WifiOff },
  unhealthy: { label: 'Unhealthy', variant: 'destructive', icon: Shield },
}

export function HealthCards() {
  const [statuses, setStatuses] = useState<ServiceHealth[]>([])

  const refresh = () => setStatuses(healthService.getAllStatuses())
  useEffect(() => { refresh(); const iv = setInterval(refresh, 10000); return () => clearInterval(iv) }, [])

  const overall = healthService.getOverallStatus()

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">System Health</h3>
        <div className="flex gap-2 text-xs text-muted-foreground">
          <span className="flex items-center gap-1"><Wifi className="h-3 w-3 text-green-400" /> {overall.healthy} Healthy</span>
          <span className="flex items-center gap-1"><AlertTriangle className="h-3 w-3 text-yellow-400" /> {overall.warning + overall.degraded} Warning</span>
          <span className="flex items-center gap-1"><Shield className="h-3 w-3 text-red-400" /> {overall.critical} Critical</span>
        </div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
        {statuses.map(s => {
          const cfg = statusConfig[s.status]
          const Icon = cfg.icon
          return (
            <Card key={s.service} className="p-2 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium truncate">{s.service}</span>
                <Badge variant={cfg.variant as any} className="text-[10px] px-1 py-0">{cfg.label}</Badge>
              </div>
              <Icon className={`h-3 w-3 ${
                s.status === 'healthy' ? 'text-green-400' :
                s.status === 'warning' || s.status === 'degraded' ? 'text-yellow-400' :
                s.status === 'critical' ? 'text-red-400' : 'text-muted-foreground'
              }`} />
              <p className="text-[10px] text-muted-foreground truncate">{s.message}</p>
              <div className="flex justify-between text-[10px] text-muted-foreground">
                <span>{s.responseTime}ms</span>
                <span>Errors: {s.errorCount}</span>
              </div>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
