import type { RecoveryRecord } from './production-types'
import { nowISO } from '../orchestration/utils'

const PREFIX = 'ajapp_rec_'

function get<T>(key: string, fallback: T): T {
  try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback } catch { return fallback }
}
function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

export const recoveryService = {
  record(workflowId: string, stage: string, success: boolean, error?: string): RecoveryRecord {
    const record: RecoveryRecord = {
      workflowId,
      stage,
      attempts: success ? 0 : 1,
      lastAttempt: nowISO(),
      success,
      error,
    }
    const history = this.getHistory(workflowId)
    history.unshift(record)
    set(PREFIX + workflowId, history.slice(0, 50))
    return record
  },

  getHistory(workflowId: string): RecoveryRecord[] {
    return get<RecoveryRecord[]>(PREFIX + workflowId, [])
  },

  getAnalytics(): { totalRecoveries: number; successRate: number; topFailedStages: { stage: string; count: number }[] } {
    const keys = Object.keys(localStorage).filter(k => k.startsWith(PREFIX))
    let total = 0; let success = 0
    const stageFailures = new Map<string, number>()
    for (const key of keys) {
      try {
        const records = JSON.parse(localStorage.getItem(key) || '[]') as RecoveryRecord[]
        for (const r of records) {
          total++
          if (r.success) success++
          else stageFailures.set(r.stage, (stageFailures.get(r.stage) || 0) + 1)
        }
      } catch {}
    }
    return {
      totalRecoveries: total,
      successRate: total > 0 ? Math.round((success / total) * 100) : 0,
      topFailedStages: Array.from(stageFailures.entries())
        .map(([stage, count]) => ({ stage, count }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 10),
    }
  },

  clearHistory(workflowId?: string): void {
    if (workflowId) {
      localStorage.removeItem(PREFIX + workflowId)
    } else {
      const keys = Object.keys(localStorage).filter(k => k.startsWith(PREFIX))
      for (const key of keys) localStorage.removeItem(key)
    }
  },
}
