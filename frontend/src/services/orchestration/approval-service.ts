import type { ApprovalEntry, ApprovalStatus, Workflow } from './types'
import { v4Service, nowISO } from './utils'

const PREFIX = 'ajapp_ork_app_'

function get<T>(key: string, fallback: T): T {
  try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback } catch { return fallback }
}
function set<T>(key: string, value: T): void { try { localStorage.setItem(key, JSON.stringify(value)) } catch {} }

export const approvalService = {
  requestApproval(workflowId: string): ApprovalEntry {
    const entry: ApprovalEntry = {
      id: v4Service.generate('appr'),
      workflowId,
      status: 'pending',
      requestedAt: nowISO(),
      decidedAt: null,
      decidedBy: null,
      comment: null,
      changes: [],
    }
    const approvals = this.getApprovals()
    approvals.push(entry)
    set(`${PREFIX}entries`, approvals)
    return entry
  },

  approve(approvalId: string, decidedBy: string = 'system', comment: string | null = null, changes: string[] = []): ApprovalEntry | null {
    return this.updateStatus(approvalId, 'approved', decidedBy, comment, changes)
  },

  reject(approvalId: string, decidedBy: string = 'system', comment: string | null = null, changes: string[] = []): ApprovalEntry | null {
    return this.updateStatus(approvalId, 'rejected', decidedBy, comment, changes)
  },

  requestChanges(approvalId: string, decidedBy: string = 'system', comment: string, changes: string[]): ApprovalEntry | null {
    return this.updateStatus(approvalId, 'changes_requested', decidedBy, comment, changes)
  },

  updateStatus(approvalId: string, status: ApprovalStatus, decidedBy: string, comment: string | null, changes: string[]): ApprovalEntry | null {
    const approvals = this.getApprovals()
    const idx = approvals.findIndex(a => a.id === approvalId)
    if (idx === -1) return null
    approvals[idx] = { ...approvals[idx], status, decidedAt: nowISO(), decidedBy, comment, changes }
    set(`${PREFIX}entries`, approvals)
    return approvals[idx]
  },

  getApprovals(): ApprovalEntry[] {
    return get<ApprovalEntry[]>(`${PREFIX}entries`, [])
  },

  getPendingApprovals(): ApprovalEntry[] {
    return this.getApprovals().filter(a => a.status === 'pending')
  },

  getForWorkflow(workflowId: string): ApprovalEntry | undefined {
    return this.getApprovals().find(a => a.workflowId === workflowId)
  },

  needsApproval(workflow: Workflow): boolean {
    return workflow.stage === 'awaiting_approval' && !this.getForWorkflow(workflow.id)
  },

  clear(): void {
    set(`${PREFIX}entries`, [])
  },
}
