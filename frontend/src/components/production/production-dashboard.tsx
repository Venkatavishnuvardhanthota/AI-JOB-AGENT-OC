import { useEffect, useState } from 'react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { HealthCards } from './health-cards'
import { MetricsPanel } from './metrics-panel'
import { AlertsPanel } from './alerts-panel'
import { ConfigEditor } from './config-editor'
import { loggingService } from '@/services/production/logging-service'
import { diagnosticsService } from '@/services/production/diagnostics-service'
import { maintenanceService } from '@/services/production/maintenance-service'
import type { LogEntry, DiagnosticReport } from '@/services/production/production-types'
import { Activity, Download, RefreshCw, FileText, Trash2, Wrench, Settings } from 'lucide-react'

export function ProductionDashboard() {
  const [activeTab, setActiveTab] = useState<'overview' | 'logs' | 'config' | 'diagnostics' | 'maintenance'>('overview')
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [logFilter, setLogFilter] = useState<string>('all')
  const [diagnostic, setDiagnostic] = useState<DiagnosticReport | null>(null)

  const refreshLogs = () => {
    switch (logFilter) {
      case 'error': setLogs(loggingService.getErrors(50)); break
      case 'info': setLogs(loggingService.getByLevel('info').slice(0, 50)); break
      case 'warn': setLogs(loggingService.getByLevel('warn').slice(0, 50)); break
      default: setLogs(loggingService.getRecent(50)); break
    }
  }

  const runDiagnostics = () => setDiagnostic(diagnosticsService.generateReport())

  useEffect(() => { if (activeTab === 'logs') refreshLogs() }, [activeTab, logFilter])

  return (
    <div className="space-y-4">
      <div className="flex gap-1 border-b border-glass-border">
        {[
          { key: 'overview', label: 'Overview', icon: Activity },
          { key: 'logs', label: 'Logs', icon: FileText },
          { key: 'config', label: 'Config', icon: Settings },
          { key: 'diagnostics', label: 'Diagnostics', icon: Wrench },
          { key: 'maintenance', label: 'Maintenance', icon: RefreshCw },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as typeof activeTab)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              activeTab === tab.key ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <div className="space-y-4">
          <HealthCards />
          <MetricsPanel />
          <AlertsPanel />
        </div>
      )}

      {activeTab === 'logs' && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">System Logs</h3>
            <div className="flex gap-1">
              {['all', 'error', 'warn', 'info'].map(f => (
                <button key={f} onClick={() => setLogFilter(f)}
                  className={`px-2 py-1 text-xs rounded-md transition-colors ${logFilter === f ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'}`}>
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
              <Button variant="ghost" size="sm" className="h-6" onClick={refreshLogs}><RefreshCw className="h-3 w-3" /></Button>
              <Button variant="ghost" size="sm" className="h-6" onClick={() => { loggingService.clear(); refreshLogs() }}><Trash2 className="h-3 w-3" /></Button>
              <Button variant="ghost" size="sm" className="h-6" onClick={() => { const blob = new Blob([loggingService.exportAsJSON()], { type: 'application/json' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = 'logs.json'; a.click(); URL.revokeObjectURL(url) }}>
                <Download className="h-3 w-3" />
              </Button>
            </div>
          </div>
          <div className="space-y-0.5 max-h-96 overflow-y-auto">
            {logs.slice(0, 100).map((entry, i) => (
              <Card key={i} className={`p-1.5 ${entry.level === 'error' ? 'bg-red-500/5 border-red-500/20' : entry.level === 'fatal' ? 'bg-red-500/10 border-red-500/30' : entry.level === 'warn' ? 'bg-yellow-500/5 border-yellow-500/20' : ''}`}>
                <div className="flex items-center gap-1">
                  <Badge variant={
                    entry.level === 'error' || entry.level === 'fatal' ? 'destructive' :
                    entry.level === 'warn' ? 'warning' : 'default'
                  } className="text-[10px] px-1 py-0">{entry.level}</Badge>
                  <span className="text-[10px] text-muted-foreground">{new Date(entry.timestamp).toLocaleTimeString()}</span>
                  {entry.service && <span className="text-[10px] text-muted-foreground">{entry.service}</span>}
                  {entry.context.correlationId && <span className="text-[10px] text-muted-foreground">corr: {entry.context.correlationId.slice(0, 8)}</span>}
                </div>
                <p className="text-xs mt-0.5">{entry.message}</p>
                {entry.error && <p className="text-[10px] text-red-400 mt-0.5">{entry.error.message}</p>}
              </Card>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'config' && <ConfigEditor />}

      {activeTab === 'diagnostics' && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">Diagnostics</h3>
            <Button size="sm" className="h-7" onClick={runDiagnostics}><RefreshCw className="h-3 w-3 mr-1" /> Run Diagnostics</Button>
          </div>
          {diagnostic && (
            <div className="space-y-2">
              <Card className="p-2 space-y-1">
                <h4 className="text-xs font-medium">System Summary</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {[
                    { label: 'Version', value: diagnostic.system.version },
                    { label: 'Uptime', value: `${Math.floor(diagnostic.system.uptime / 60)}m` },
                    { label: 'Services', value: `${diagnostic.system.healthyServices}/${diagnostic.system.totalServices} healthy` },
                    { label: 'Degraded', value: diagnostic.system.degradedServices },
                  ].map(d => (
                    <div key={d.label} className="text-center">
                      <p className="text-[10px] text-muted-foreground">{d.label}</p>
                      <p className="text-sm font-bold">{d.value}</p>
                    </div>
                  ))}
                </div>
              </Card>

              <Card className="p-2 space-y-1">
                <h4 className="text-xs font-medium">Recommendations</h4>
                <ul className="list-disc list-inside space-y-0.5">
                  {diagnostic.recommendations.map((r, i) => (
                    <li key={i} className="text-[10px] text-muted-foreground">{r}</li>
                  ))}
                </ul>
              </Card>

              <Card className="p-2 space-y-1">
                <h4 className="text-xs font-medium">Dependencies</h4>
                {diagnostic.dependencies.map(d => (
                  <div key={d.name} className="flex items-center justify-between py-0.5">
                    <span className="text-[10px]">{d.name} <span className="text-muted-foreground">v{d.version}</span></span>
                    <Badge variant="success" className="text-[10px] px-1 py-0">{d.status}</Badge>
                  </div>
                ))}
              </Card>
            </div>
          )}
          {!diagnostic && (
            <div className="text-center py-12 text-muted-foreground">
              <p className="text-sm">Click "Run Diagnostics" to generate a system report.</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'maintenance' && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">Maintenance Tasks</h3>
            <Button size="sm" className="h-7" onClick={() => { maintenanceService.runAll(); refreshLogs() }}>
              <RefreshCw className="h-3 w-3 mr-1" /> Run All Tasks
            </Button>
          </div>
          <div className="space-y-1">
            {maintenanceService.getTasks().map(task => (
              <Card key={task.id} className="p-2 flex items-center justify-between">
                <div className="flex-1 min-w-0 mr-2">
                  <div className="flex items-center gap-1">
                    <span className="text-xs font-medium">{task.name}</span>
                    <span className="text-[10px] text-muted-foreground">({task.type})</span>
                    <Badge variant={task.enabled ? 'success' : 'secondary'} className="text-[10px] px-1 py-0">{task.enabled ? 'Active' : 'Paused'}</Badge>
                  </div>
                  <p className="text-[10px] text-muted-foreground">Retention: {task.retentionDays}d | Interval: {Math.floor(task.interval / 3600)}h | Last: {task.lastRun ? new Date(task.lastRun).toLocaleString() : 'Never'}</p>
                </div>
                <div className="flex gap-1 shrink-0">
                  <Button variant="ghost" size="sm" className="h-6 text-xs" onClick={() => { maintenanceService.toggleTask(task.id); refreshLogs() }}>
                    {task.enabled ? 'Pause' : 'Resume'}
                  </Button>
                  <Button variant="ghost" size="sm" className="h-6 text-xs" onClick={() => { maintenanceService.runTask(task.id); refreshLogs() }}>
                    Run
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
