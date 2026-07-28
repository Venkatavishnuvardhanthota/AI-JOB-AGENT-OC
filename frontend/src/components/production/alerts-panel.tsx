import { useEffect, useState } from 'react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { alertService } from '@/services/production/alert-service'
import type { Alert } from '@/services/production/production-types'
import { BellOff, CheckCircle, Eye } from 'lucide-react'

const severityVariant: Record<string, string> = {
  info: 'default',
  warning: 'warning',
  error: 'destructive',
  critical: 'destructive',
}

export function AlertsPanel() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [filter, setFilter] = useState<'all' | 'active' | 'critical'>('active')

  const refresh = () => {
    switch (filter) {
      case 'active': setAlerts(alertService.getActive()); break
      case 'critical': setAlerts(alertService.getCriticalUnresolved()); break
      default: setAlerts(alertService.getRecent(50)); break
    }
  }
  useEffect(() => { refresh(); const iv = setInterval(refresh, 10000); return () => clearInterval(iv) }, [filter])

  const counts = alertService.getAlertCounts()

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">Alerts</h3>
        <div className="flex gap-1">
          {(['active', 'critical', 'all'] as const).map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className={`px-2 py-1 text-xs rounded-md transition-colors ${filter === f ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'}`}>
              {f.charAt(0).toUpperCase() + f.slice(1)}
              {f === 'active' && <span className="ml-1 text-[10px]">({counts.active})</span>}
              {f === 'critical' && <span className="ml-1 text-[10px]">({counts.total - counts.resolved})</span>}
            </button>
          ))}
        </div>
      </div>

      {alerts.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          <BellOff className="h-6 w-6 mx-auto mb-2 opacity-50" />
          <p className="text-xs">No {filter !== 'all' ? filter : ''} alerts.</p>
        </div>
      )}

      <div className="space-y-1 max-h-80 overflow-y-auto">
        {alerts.slice(0, 30).map(alert => (
          <Card key={alert.id} className="p-2 flex items-start justify-between">
            <div className="flex-1 min-w-0 mr-2">
              <div className="flex items-center gap-1">
                <Badge variant={severityVariant[alert.severity] as any} className="text-[10px] px-1 py-0">{alert.severity}</Badge>
                <span className="text-xs font-medium truncate">{alert.title}</span>
              </div>
              <p className="text-[10px] text-muted-foreground truncate mt-0.5">{alert.message}</p>
              <div className="flex gap-2 text-[10px] text-muted-foreground mt-0.5">
                <span>{alert.service}</span>
                <span>{new Date(alert.timestamp).toLocaleString()}</span>
              </div>
            </div>
            <div className="flex gap-0.5 shrink-0">
              {alert.status === 'active' && (
                <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={() => { alertService.acknowledge(alert.id); refresh() }}>
                  <Eye className="h-3 w-3" />
                </Button>
              )}
              {(alert.status === 'active' || alert.status === 'acknowledged') && (
                <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={() => { alertService.resolve(alert.id); refresh() }}>
                  <CheckCircle className="h-3 w-3" />
                </Button>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
