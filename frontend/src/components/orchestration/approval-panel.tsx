import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { approvalService } from '@/services/orchestration/approval-service'
import { workflowOrchestrator } from '@/services/orchestration/workflow-orchestrator'
import type { ApprovalEntry } from '@/services/orchestration/types'
import { CheckCircle, XCircle, Edit3 } from 'lucide-react'

export function ApprovalPanel() {
  const [approvals, setApprovals] = useState<ApprovalEntry[]>([])

  const refresh = () => setApprovals(approvalService.getPendingApprovals())
  useEffect(() => { refresh(); const iv = setInterval(refresh, 5000); return () => clearInterval(iv) }, [])

  const handleApprove = (entry: ApprovalEntry) => {
    approvalService.approve(entry.id, 'user', 'Approved via dashboard')
    const wf = workflowOrchestrator.getWorkflow(entry.workflowId)
    if (wf) workflowOrchestrator.transition(wf.id, 'submitting')
    refresh()
  }

  const handleReject = (entry: ApprovalEntry) => {
    approvalService.reject(entry.id, 'user', 'Rejected via dashboard')
    refresh()
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium">Pending Approvals ({approvals.length})</h3>
      {approvals.length === 0 && (
        <p className="text-sm text-muted-foreground py-8 text-center">No pending approvals.</p>
      )}
      {approvals.map(entry => {
        const wf = workflowOrchestrator.getWorkflow(entry.workflowId)
        return (
          <Card key={entry.id} className="p-3 space-y-2">
            <div className="flex items-start justify-between">
              <div>
                <h4 className="text-sm font-medium">{wf?.jobTitle || 'Unknown'}</h4>
                <p className="text-xs text-muted-foreground">{wf?.companyName || 'Unknown'}</p>
              </div>
              <Badge variant="warning">Pending</Badge>
            </div>
            <p className="text-xs text-muted-foreground">Requested at: {new Date(entry.requestedAt).toLocaleString()}</p>
            <div className="flex justify-end gap-1">
              <Button variant="ghost" size="sm" onClick={() => handleApprove(entry)}><CheckCircle className="h-4 w-4 text-green-400" /></Button>
              <Button variant="ghost" size="sm" onClick={() => handleReject(entry)}><XCircle className="h-4 w-4 text-red-400" /></Button>
              <Button variant="ghost" size="sm"><Edit3 className="h-4 w-4" /></Button>
            </div>
          </Card>
        )
      })}
    </div>
  )
}
