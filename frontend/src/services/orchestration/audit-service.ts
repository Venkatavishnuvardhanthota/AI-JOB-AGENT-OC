import type { AuditEntry, AuditSeverity, WorkflowStage } from './types'
import { v4Service, nowISO } from './utils'

const PREFIX = 'ajapp_ork_aud_'

function get<T>(key: string, fallback: T): T { try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback } catch { return fallback } }
function set<T>(key: string, value: T): void { try { localStorage.setItem(key, JSON.stringify(value)) } catch {} }

export const auditService = {
  record(workflowId: string, stage: WorkflowStage, action: string, message: string, severity: AuditSeverity = 'info', data: Record<string, unknown> | null = null): AuditEntry {
    const entry: AuditEntry = { id: v4Service.generate('aud'), workflowId, stage, action, severity, message, data, timestamp: nowISO() }
    const entries = this.getEntries(workflowId)
    entries.unshift(entry)
    set(`${PREFIX}${workflowId}`, entries.slice(0, 500))
    return entry
  },

  getEntries(workflowId: string): AuditEntry[] {
    return get<AuditEntry[]>(`${PREFIX}${workflowId}`, [])
  },

  search(query: string): AuditEntry[] {
    const results: AuditEntry[] = []
    const keys = Object.keys(localStorage).filter(k => k.startsWith(PREFIX))
    for (const key of keys) {
      try {
        const entries = JSON.parse(localStorage.getItem(key) || '[]') as AuditEntry[]
        for (const entry of entries) {
          if (entry.message.toLowerCase().includes(query.toLowerCase()) || entry.action.toLowerCase().includes(query.toLowerCase())) {
            results.push(entry)
          }
        }
      } catch {}
    }
    return results.sort((a, b) => b.timestamp.localeCompare(a.timestamp)).slice(0, 100)
  },

  getRecent(count: number = 50): AuditEntry[] {
    const all: AuditEntry[] = []
    const keys = Object.keys(localStorage).filter(k => k.startsWith(PREFIX))
    for (const key of keys) {
      try {
        const entries = JSON.parse(localStorage.getItem(key) || '[]') as AuditEntry[]
        all.push(...entries)
      } catch {}
    }
    return all.sort((a, b) => b.timestamp.localeCompare(a.timestamp)).slice(0, count)
  },

  clear(workflowId: string): void {
    set(`${PREFIX}${workflowId}`, [])
  },
}
