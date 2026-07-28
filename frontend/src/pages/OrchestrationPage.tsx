import { useState } from 'react'
import { PageHeader } from '@/components/layout/page-header'
import { OrchestrationDashboard } from '@/components/orchestration/orchestration-dashboard'
import { WorkflowList } from '@/components/orchestration/workflow-list'
import { ApprovalPanel } from '@/components/orchestration/approval-panel'
import { workflowOrchestrator } from '@/services/orchestration/workflow-orchestrator'
import { Layers, ListTodo, CheckSquare, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function OrchestrationPage() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'workflows' | 'approvals'>('dashboard')

  const handleCreateDemo = () => {
    const wf = workflowOrchestrator.createWorkflow('Senior Software Engineer', 'TechCorp', 0.85, 78, 1)
    workflowOrchestrator.transition(wf.id, 'matched')
    workflowOrchestrator.transition(wf.id, 'generating')
    workflowOrchestrator.transition(wf.id, 'generated')
    workflowOrchestrator.queueForProcessing(wf.id)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Orchestration"
        description="Monitor and manage autonomous job application workflows."
        actions={
          <Button size="sm" onClick={handleCreateDemo}>
            <Plus className="h-4 w-4 mr-1" /> Create Demo Workflow
          </Button>
        }
      />

      <div className="flex gap-1 border-b border-glass-border">
        {[
          { key: 'dashboard', label: 'Dashboard', icon: Layers },
          { key: 'workflows', label: 'Workflows', icon: ListTodo },
          { key: 'approvals', label: 'Approvals', icon: CheckSquare },
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

      {activeTab === 'dashboard' && <OrchestrationDashboard />}
      {activeTab === 'workflows' && <WorkflowList />}
      {activeTab === 'approvals' && <ApprovalPanel />}
    </div>
  )
}
