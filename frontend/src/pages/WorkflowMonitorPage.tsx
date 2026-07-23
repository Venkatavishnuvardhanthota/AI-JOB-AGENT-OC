import { PageHeader } from '@/components/layout/page-header'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Activity, CheckCircle, Clock, AlertTriangle, Loader2 } from 'lucide-react'

const mockPipelines = [
  { id: '1', name: 'Daily Job Discovery', status: 'running', stage: 'Searching providers...', started: '2 min ago', progress: 65 },
  { id: '2', name: 'Application Processing', status: 'completed', stage: 'Done', started: '1 hour ago', progress: 100 },
  { id: '3', name: 'Profile Sync', status: 'paused', stage: 'Waiting for resume', started: '30 min ago', progress: 45 },
  { id: '4', name: 'Match Scoring', status: 'failed', stage: 'Provider timeout', started: '2 hours ago', progress: 30 },
]

export function WorkflowMonitorPage() {
  const statusIcon = (status: string) => {
    switch (status) {
      case 'running': return <Loader2 className="h-4 w-4 text-primary animate-spin" />;
      case 'completed': return <CheckCircle className="h-4 w-4 text-success" />;
      case 'paused': return <Clock className="h-4 w-4 text-warning" />;
      case 'failed': return <AlertTriangle className="h-4 w-4 text-error" />;
      default: return <Activity className="h-4 w-4 text-muted-foreground" />;
    }
  }

  const statusBadge = (status: string) => {
    const variants: Record<string, 'success' | 'warning' | 'default' | 'destructive'> = {
      running: 'default', completed: 'success', paused: 'warning', failed: 'destructive',
    }
    return <Badge variant={variants[status] || 'secondary'}>{status}</Badge>
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Workflow Monitor" description="Real-time status of pipeline executions." />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardContent className="p-4 text-center"><div className="text-2xl font-bold text-primary">4</div><div className="text-xs text-muted-foreground">Total</div></CardContent></Card>
        <Card><CardContent className="p-4 text-center"><div className="text-2xl font-bold text-success">1</div><div className="text-xs text-muted-foreground">Completed</div></CardContent></Card>
        <Card><CardContent className="p-4 text-center"><div className="text-2xl font-bold text-warning">1</div><div className="text-xs text-muted-foreground">Running</div></CardContent></Card>
        <Card><CardContent className="p-4 text-center"><div className="text-2xl font-bold text-error">1</div><div className="text-xs text-muted-foreground">Failed</div></CardContent></Card>
      </div>

      <div className="space-y-3">
        {mockPipelines.map(p => (
          <Card key={p.id}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  {statusIcon(p.status)}
                  <div>
                    <h3 className="font-medium text-sm">{p.name}</h3>
                    <p className="text-xs text-muted-foreground">{p.started} · {p.stage}</p>
                  </div>
                </div>
                {statusBadge(p.status)}
              </div>
              <div className="h-2 rounded-full bg-dark-800 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    p.status === 'completed' ? 'bg-success' :
                    p.status === 'running' ? 'bg-primary' :
                    p.status === 'failed' ? 'bg-error' : 'bg-warning'
                  }`}
                  style={{ width: `${p.progress}%` }}
                />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
