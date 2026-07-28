import type { MaintenanceTask } from './production-types'
import { v4Service, nowISO } from '../orchestration/utils'
import { loggingService } from './logging-service'

const PREFIX = 'ajapp_mnt_'
const TASKS_KEY = PREFIX + 'tasks'

function get<T>(key: string, fallback: T): T {
  try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback } catch { return fallback }
}
function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

function isOlderThan(dateStr: string, days: number): boolean {
  const date = new Date(dateStr)
  const cutoff = Date.now() - days * 24 * 60 * 60 * 1000
  return date.getTime() < cutoff
}

const DEFAULT_TASKS: Omit<MaintenanceTask, 'id'>[] = [
  { name: 'Prune Old Logs', type: 'prune', target: 'logs', lastRun: null, nextRun: null, interval: 86400, enabled: true, retentionDays: 30 },
  { name: 'Prune Old Metrics', type: 'prune', target: 'metrics', lastRun: null, nextRun: null, interval: 86400, enabled: true, retentionDays: 90 },
  { name: 'Prune Old Alerts', type: 'prune', target: 'alerts', lastRun: null, nextRun: null, interval: 86400, enabled: true, retentionDays: 60 },
  { name: 'Cleanup History', type: 'cleanup', target: 'workflow-history', lastRun: null, nextRun: null, interval: 86400, enabled: true, retentionDays: 180 },
  { name: 'Cleanup Browser Sessions', type: 'cleanup', target: 'browser-sessions', lastRun: null, nextRun: null, interval: 3600, enabled: true, retentionDays: 7 },
  { name: 'Cleanup Screenshots', type: 'cleanup', target: 'screenshots', lastRun: null, nextRun: null, interval: 86400, enabled: true, retentionDays: 30 },
  { name: 'Prune Temp Files', type: 'prune', target: 'temp', lastRun: null, nextRun: null, interval: 3600, enabled: true, retentionDays: 1 },
  { name: 'Rotate Logs', type: 'rotate', target: 'logs', lastRun: null, nextRun: null, interval: 86400, enabled: true, retentionDays: 30 },
  { name: 'Compact Storage', type: 'compress', target: 'localStorage', lastRun: null, nextRun: null, interval: 604800, enabled: true, retentionDays: 365 },
]

export const maintenanceService = {
  getTasks(): MaintenanceTask[] {
    let tasks = get<MaintenanceTask[]>(TASKS_KEY, [])
    if (tasks.length === 0) {
      tasks = DEFAULT_TASKS.map(t => ({ ...t, id: v4Service.generate('mnt') }))
      set(TASKS_KEY, tasks)
    }
    return tasks
  },

  updateTask(id: string, updates: Partial<MaintenanceTask>): MaintenanceTask | null {
    const tasks = this.getTasks()
    const idx = tasks.findIndex(t => t.id === id)
    if (idx === -1) return null
    tasks[idx] = { ...tasks[idx], ...updates }
    set(TASKS_KEY, tasks)
    return tasks[idx]
  },

  toggleTask(id: string): MaintenanceTask | null {
    const task = this.getTasks().find(t => t.id === id)
    if (!task) return null
    return this.updateTask(id, { enabled: !task.enabled })
  },

  runTask(id: string): { success: boolean; message: string; itemsRemoved?: number } {
    const task = this.getTasks().find(t => t.id === id)
    if (!task) return { success: false, message: 'Task not found' }

    const now = nowISO()
    let itemsRemoved = 0

    try {
      switch (task.target) {
        case 'logs':
          itemsRemoved = this.pruneLogs(task.retentionDays)
          break
        case 'metrics':
          itemsRemoved = this.pruneMetrics(task.retentionDays)
          break
        case 'alerts':
          itemsRemoved = this.pruneAlerts(task.retentionDays)
          break
        case 'workflow-history':
          itemsRemoved = this.pruneHistory(task.retentionDays)
          break
        case 'browser-sessions':
          itemsRemoved = this.pruneBrowserSessions(task.retentionDays)
          break
        case 'screenshots':
          itemsRemoved = this.pruneScreenshots(task.retentionDays)
          break
        case 'temp':
          itemsRemoved = this.pruneTempFiles()
          break
        case 'localStorage':
          itemsRemoved = this.compactStorage()
          break
        default:
          break
      }

      this.updateTask(id, { lastRun: now, nextRun: new Date(Date.now() + task.interval * 1000).toISOString() })
      loggingService.info(`Maintenance: ${task.name} completed`, undefined, { itemsRemoved, taskId: id, target: task.target })
      return { success: true, message: `${task.name} completed - removed ${itemsRemoved} items`, itemsRemoved }
    } catch (err) {
      loggingService.error(`Maintenance: ${task.name} failed`, err as Error, undefined, { taskId: id, target: task.target })
      return { success: false, message: `${task.name} failed: ${err instanceof Error ? err.message : 'Unknown error'}` }
    }
  },

  runAll(): { success: number; failed: number; results: { task: string; success: boolean; message: string }[] } {
    const tasks = this.getTasks().filter(t => t.enabled)
    let success = 0; let failed = 0
    const results: { task: string; success: boolean; message: string }[] = []
    for (const task of tasks) {
      const result = this.runTask(task.id)
      if (result.success) success++; else failed++
      results.push({ task: task.name, success: result.success, message: result.message })
    }
    return { success, failed, results }
  },

  getOverdueTasks(): MaintenanceTask[] {
    const now = new Date()
    return this.getTasks().filter(t => t.enabled && (t.nextRun === null || new Date(t.nextRun) <= now))
  },

  pruneLogs(retentionDays: number): number {
    const key = 'ajapp_log_entries'
    try {
      const entries = JSON.parse(localStorage.getItem(key) || '[]') as { timestamp: string }[]
      const filtered = entries.filter(e => !isOlderThan(e.timestamp, retentionDays))
      localStorage.setItem(key, JSON.stringify(filtered))
      return entries.length - filtered.length
    } catch { return 0 }
  },

  pruneMetrics(retentionDays: number): number {
    let total = 0
    const keys = Object.keys(localStorage).filter(k => k.startsWith('ajapp_met_'))
    for (const key of keys) {
      try {
        const samples = JSON.parse(localStorage.getItem(key) || '[]') as { timestamp: string }[]
        const filtered = samples.filter(s => !isOlderThan(s.timestamp, retentionDays))
        localStorage.setItem(key, JSON.stringify(filtered))
        total += samples.length - filtered.length
      } catch {}
    }
    return total
  },

  pruneAlerts(retentionDays: number): number {
    try {
      const alerts = JSON.parse(localStorage.getItem('ajapp_alert_alerts') || '[]') as { timestamp: string; resolvedAt?: string }[]
      const filtered = alerts.filter(a => {
        if (a.resolvedAt) return !isOlderThan(a.resolvedAt, retentionDays)
        return !isOlderThan(a.timestamp, retentionDays)
      })
      localStorage.setItem('ajapp_alert_alerts', JSON.stringify(filtered))
      return alerts.length - filtered.length
    } catch { return 0 }
  },

  pruneHistory(retentionDays: number): number {
    let total = 0
    const keys = Object.keys(localStorage).filter(k => k.startsWith('ajapp_ork_q_'))
    for (const key of keys) {
      try {
        const queue = JSON.parse(localStorage.getItem(key) || '[]') as { enqueuedAt: string }[]
        const filtered = queue.filter(e => !isOlderThan(e.enqueuedAt, retentionDays))
        localStorage.setItem(key, JSON.stringify(filtered))
        total += queue.length - filtered.length
      } catch {}
    }
    return total
  },

  pruneBrowserSessions(retentionDays: number): number {
    const key = 'ajapp_browser_sessions'
    try {
      const sessions = JSON.parse(localStorage.getItem(key) || '[]') as { startedAt: string }[]
      const filtered = sessions.filter(s => !isOlderThan(s.startedAt, retentionDays))
      localStorage.setItem(key, JSON.stringify(filtered))
      return sessions.length - filtered.length
    } catch { return 0 }
  },

  pruneScreenshots(retentionDays: number): number {
    const key = 'ajapp_browser_screenshots'
    try {
      const screenshots = JSON.parse(localStorage.getItem(key) || '[]') as { capturedAt: string }[]
      const filtered = screenshots.filter(s => !isOlderThan(s.capturedAt, retentionDays))
      localStorage.setItem(key, JSON.stringify(filtered))
      return screenshots.length - filtered.length
    } catch { return 0 }
  },

  pruneTempFiles(): number {
    const keysToRemove = Object.keys(localStorage).filter(k =>
      k.startsWith('ajapp_temp_') || k.startsWith('ajapp_tmp_')
    )
    for (const key of keysToRemove) localStorage.removeItem(key)
    return keysToRemove.length
  },

  compactStorage(): number {
    let count = 0
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key && key.startsWith('ajapp_')) {
        try {
          const val = localStorage.getItem(key)
          if (val) {
            const parsed = JSON.parse(val)
            const compacted = JSON.stringify(parsed)
            localStorage.setItem(key, compacted)
          }
        } catch {}
      }
    }
    return count
  },
}
