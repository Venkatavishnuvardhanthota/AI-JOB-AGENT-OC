import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { monitoringService } from '@/services/browser/monitoring-service'
import type { BrowserMonitoringReport } from '@/services/browser/types'
import { Shield, AlertTriangle, CheckCircle } from 'lucide-react'

export function BrowserMonitor() {
  const [reports, setReports] = useState<BrowserMonitoringReport[]>([])

  useEffect(() => {
    setReports(monitoringService.getAllReports())
    const iv = setInterval(() => setReports(monitoringService.getAllReports()), 5000)
    return () => clearInterval(iv)
  }, [])

  const health = monitoringService.getOverallHealth()

  return (
    <Card className="p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-muted-foreground" />
          <h3 className="text-sm font-medium">Monitoring</h3>
        </div>
        <Badge variant={health.ok ? 'success' : 'warning'}>
          {health.ok ? <CheckCircle className="h-3 w-3 mr-1 inline" /> : <AlertTriangle className="h-3 w-3 mr-1 inline" />}
          {health.ok ? 'Healthy' : 'Issues Detected'}
        </Badge>
      </div>

      <div className="grid grid-cols-3 gap-3 text-center">
        <div>
          <p className="text-lg font-bold">{health.activeBrowsers}</p>
          <p className="text-xs text-muted-foreground">Active Browsers</p>
        </div>
        <div>
          <p className="text-lg font-bold">{health.totalErrors}</p>
          <p className="text-xs text-muted-foreground">Total Errors</p>
        </div>
        <div>
          <p className="text-lg font-bold">{health.warnings.length}</p>
          <p className="text-xs text-muted-foreground">Warnings</p>
        </div>
      </div>

      {reports.length === 0 && (
        <p className="text-xs text-muted-foreground text-center py-2">No browser instances to monitor.</p>
      )}

      {reports.map(r => (
        <div key={r.browserId} className="text-xs text-muted-foreground border-t border-glass-border pt-2">
          <span className="font-medium text-foreground">{r.browserId}</span>
          <span className="ml-2">Sessions: {r.sessions} | Success: {r.successRate}% | Avg Nav: {r.averageNavigationTime}ms</span>
        </div>
      ))}
    </Card>
  )
}
