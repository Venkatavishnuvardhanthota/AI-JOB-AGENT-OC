import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { workflowOrchestrator } from '@/services/orchestration/workflow-orchestrator'
import { getStageLabel, getStageColor } from '@/services/orchestration/workflow-state'
import type { Workflow } from '@/services/orchestration/types'
import { Play, Pause, XCircle, Clock } from 'lucide-react'

export function WorkflowList() {
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [filter, setFilter] = useState<string>('all')

  const refresh = () => setWorkflows(workflowOrchestrator.getAllWorkflows())
  useEffect(() => { refresh(); const iv = setInterval(refresh, 5000); return () => clearInterval(iv) }, [])

  const filtered = filter === 'all' ? workflows : workflows.filter(w => w.status === filter)

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <h3 className="text-sm font-medium">Workflows ({workflows.length})</h3>
        <div className="flex gap-1 ml-auto">
          {['all', 'running', 'paused', 'failed', 'completed'].map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className={`px-2 py-1 text-xs rounded-md transition-colors ${filter === f ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'}`}>
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          <Clock className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No workflows {filter !== 'all' ? `with status "${filter}"` : ''}.</p>
        </div>
      )}

      {filtered.slice(0, 30).map(wf => (
        <Card key={wf.id} className="p-3 space-y-2">
          <div className="flex items-start justify-between">
            <div>
              <h4 className="text-sm font-medium">{wf.jobTitle}</h4>
              <p className="text-xs text-muted-foreground">{wf.companyName}</p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={getStageColor(wf.stage) as any}>{getStageLabel(wf.stage)}</Badge>
            </div>
          </div>
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span>Match: {Math.round(wf.matchScore * 100)}%</span>
            <span>Confidence: {wf.confidence}%</span>
            <span>Priority: {wf.priority}</span>
            <span>Retries: {wf.retryCount}/{wf.maxRetries}</span>
          </div>
          <div className="flex justify-end gap-1">
            {wf.status === 'paused' && <Button variant="ghost" size="sm" onClick={() => { workflowOrchestrator.resumeWorkflow(wf.id); refresh() }}><Play className="h-4 w-4" /></Button>}
            {wf.status === 'running' && <Button variant="ghost" size="sm" onClick={() => { workflowOrchestrator.pauseWorkflow(wf.id); refresh() }}><Pause className="h-4 w-4" /></Button>}
            {wf.status !== 'completed' && wf.status !== 'cancelled' && (
              <Button variant="ghost" size="sm" onClick={() => { workflowOrchestrator.cancelWorkflow(wf.id); refresh() }}><XCircle className="h-4 w-4" /></Button>
            )}
          </div>
        </Card>
      ))}
    </div>
  )
}
