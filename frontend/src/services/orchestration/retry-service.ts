import type { RetryRecord, WorkflowStage } from './types'
import { computeBackoffDelay, nowISO } from './utils'

const PREFIX = 'ajapp_ork_ret_'

function get<T>(key: string, fallback: T): T { try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback } catch { return fallback } }
function set<T>(key: string, value: T): void { try { localStorage.setItem(key, JSON.stringify(value)) } catch {} }

export const retryService = {
  shouldRetry(retryCount: number, maxRetries: number): boolean {
    return retryCount < maxRetries
  },

  computeDelay(retryCount: number, baseDelay: number = 1000, maxDelay: number = 30000, factor: number = 2): number {
    return computeBackoffDelay(baseDelay, maxDelay, factor, retryCount + 1)
  },

  record(workflowId: string, stage: WorkflowStage, reason: string, delay: number, success: boolean): RetryRecord {
    const record: RetryRecord = {
      attempt: this.getHistory(workflowId).length + 1,
      stage,
      reason,
      delay,
      timestamp: nowISO(),
      success,
    }
    const history = this.getHistory(workflowId)
    history.push(record)
    set(`${PREFIX}${workflowId}`, history.slice(-100))
    return record
  },

  getHistory(workflowId: string): RetryRecord[] {
    return get<RetryRecord[]>(`${PREFIX}${workflowId}`, [])
  },

  getTotalRetries(): number {
    let total = 0
    const keys = Object.keys(localStorage).filter(k => k.startsWith(PREFIX))
    for (const key of keys) {
      try {
        const records = JSON.parse(localStorage.getItem(key) || '[]') as RetryRecord[]
        total += records.length
      } catch {}
    }
    return total
  },

  getRetryAnalytics(): { totalRetries: number; successRate: number; avgAttempts: number } {
    let total = 0; let success = 0; let workflows = 0
    const keys = Object.keys(localStorage).filter(k => k.startsWith(PREFIX))
    for (const key of keys) {
      try {
        const records = JSON.parse(localStorage.getItem(key) || '[]') as RetryRecord[]
        if (records.length > 0) { total += records.length; success += records.filter(r => r.success).length; workflows++ }
      } catch {}
    }
    return { totalRetries: total, successRate: total > 0 ? Math.round((success / total) * 100) : 0, avgAttempts: workflows > 0 ? Math.round(total / workflows) : 0 }
  },

  clearHistory(workflowId: string): void {
    set(`${PREFIX}${workflowId}`, [])
  },
}
