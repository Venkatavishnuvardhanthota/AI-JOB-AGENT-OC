import { PageHeader } from '@/components/layout/page-header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Activity, AlertTriangle, Cpu, Database, Brain, Server, BarChart3 } from 'lucide-react'

const healthChecks = [
  { name: 'Application Server', status: 'healthy', icon: Server },
  { name: 'Database', status: 'healthy', icon: Database },
  { name: 'AI Service', status: 'degraded', icon: Brain },
  { name: 'Orchestrator', status: 'healthy', icon: Cpu },
]

const metrics = [
  { label: 'Avg Response Time', value: '245ms', trend: '+12%' },
  { label: 'Error Rate', value: '0.3%', trend: '-0.1%' },
  { label: 'Throughput', value: '1.2k req/min', trend: '+8%' },
  { label: 'Active Pipelines', value: '3', trend: '0' },
]

export function OperationsPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Operations" description="System health, metrics, and diagnostics." />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {healthChecks.map(hc => (
          <Card key={hc.name}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <hc.icon className="h-5 w-5 text-muted-foreground" />
                <div className={`h-2 w-2 rounded-full ${hc.status === 'healthy' ? 'bg-success' : 'bg-warning'}`} />
              </div>
              <p className="text-sm font-medium">{hc.name}</p>
              <p className={`text-xs ${hc.status === 'healthy' ? 'text-success' : 'text-warning'}`}>{hc.status}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            Key Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {metrics.map(m => (
              <div key={m.label} className="text-center p-4 rounded-lg bg-dark-800/50">
                <p className="text-2xl font-bold">{m.value}</p>
                <p className="text-xs text-muted-foreground mt-1">{m.label}</p>
                <p className="text-xs text-muted-foreground">{m.trend}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" />
            Diagnostics Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { severity: 'warning', message: 'Slow stage detected: "provider_search" (avg 12.3s)', count: 5 },
              { severity: 'info', message: 'High retry count for provider "Workday"', count: 3 },
              { severity: 'error', message: 'AI service returned timeout errors', count: 2 },
            ].map((d, i) => (
              <div key={i} className={`flex items-center justify-between p-3 rounded-lg ${
                d.severity === 'error' ? 'bg-error/5 border border-error/20' :
                d.severity === 'warning' ? 'bg-warning/5 border border-warning/20' :
                'bg-dark-800/30'
              }`}>
                <div className="flex items-center gap-2">
                  <AlertTriangle className={`h-4 w-4 ${
                    d.severity === 'error' ? 'text-error' : d.severity === 'warning' ? 'text-warning' : 'text-muted-foreground'
                  }`} />
                  <span className="text-sm">{d.message}</span>
                </div>
                <Badge variant={d.severity === 'error' ? 'destructive' : d.severity === 'warning' ? 'warning' : 'secondary'}>
                  x{d.count}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}