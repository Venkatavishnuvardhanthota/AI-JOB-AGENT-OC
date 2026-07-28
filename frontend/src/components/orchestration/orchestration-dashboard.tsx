import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { workflowDashboardService } from '@/services/orchestration/dashboard-service'
import { Play, PauseCircle, CheckCircle, AlertCircle, Clock, RefreshCw } from 'lucide-react'

export function OrchestrationDashboard() {
  const [data, setData] = useState(() => workflowDashboardService.getDashboardData())

  useEffect(() => {
    const iv = setInterval(() => setData(workflowDashboardService.getDashboardData()), 3000)
    return () => clearInterval(iv)
  }, [])

  const cards = [
    { label: 'Running', value: data.running, icon: Play, color: 'text-green-400' },
    { label: 'Queued', value: data.queued, icon: Clock, color: 'text-blue-400' },
    { label: 'Paused', value: data.paused, icon: PauseCircle, color: 'text-yellow-400' },
    { label: 'Completed', value: data.completed, icon: CheckCircle, color: 'text-green-400' },
    { label: 'Failed', value: data.failed, icon: AlertCircle, color: 'text-red-400' },
    { label: 'Pending Approval', value: data.pendingApprovals, icon: RefreshCw, color: 'text-purple-400' },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {cards.map(card => (
        <Card key={card.label} className="p-4 flex items-center gap-3">
          <card.icon className={`h-8 w-8 ${card.color}`} />
          <div>
            <p className="text-2xl font-bold">{card.value}</p>
            <p className="text-xs text-muted-foreground">{card.label}</p>
          </div>
        </Card>
      ))}
    </div>
  )
}
