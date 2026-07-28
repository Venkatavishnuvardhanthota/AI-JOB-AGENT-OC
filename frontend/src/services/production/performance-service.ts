import type { PerformanceSample, ServiceName } from './production-types'
import { nowISO } from '../orchestration/utils'
import { metricsService } from './metrics-service'
import { loggingService } from './logging-service'

const PREFIX = 'ajapp_perf_'

function get<T>(key: string, fallback: T): T {
  try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback } catch { return fallback }
}
function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

export const performanceService = {
  record(operation: string, duration: number, service: ServiceName = 'workflow-engine', tags: Record<string, string> = {}, success: boolean = true): PerformanceSample {
    const sample: PerformanceSample = { operation, duration, timestamp: nowISO(), service, tags, success }

    metricsService.recordDuration(`perf.${operation}`, duration, tags, service)
    if (!success) metricsService.increment(`perf.${operation}.failures`, tags, service)

    const history = this.getHistory(operation)
    history.push(sample)
    set(PREFIX + operation, history.slice(-1000))

    if (duration > 5000) {
      loggingService.warn(`Slow operation: ${operation} took ${duration}ms`, undefined, { operation, duration, service }, service)
    }

    return sample
  },

  getHistory(operation: string): PerformanceSample[] {
    return get<PerformanceSample[]>(PREFIX + operation, [])
  },

  getRecentOperations(limit: number = 50): PerformanceSample[] {
    const keys = Object.keys(localStorage).filter(k => k.startsWith(PREFIX))
    const all: PerformanceSample[] = []
    for (const key of keys) {
      try {
        const samples = JSON.parse(localStorage.getItem(key) || '[]') as PerformanceSample[]
        all.push(...samples)
      } catch {}
    }
    return all.sort((a, b) => b.timestamp.localeCompare(a.timestamp)).slice(0, limit)
  },

  getAverageDuration(operation: string): number {
    const history = this.getHistory(operation)
    if (history.length === 0) return 0
    const recent = history.slice(-100)
    return Math.round(recent.reduce((sum, s) => sum + s.duration, 0) / recent.length)
  },

  getSlowestOperations(minSamples: number = 5): { operation: string; avgDuration: number; maxDuration: number; count: number }[] {
    const keys = Object.keys(localStorage).filter(k => k.startsWith(PREFIX))
    const results: { operation: string; avgDuration: number; maxDuration: number; count: number }[] = []
    for (const key of keys) {
      try {
        const samples = JSON.parse(localStorage.getItem(key) || '[]') as PerformanceSample[]
        if (samples.length >= minSamples) {
          const durations = samples.map(s => s.duration)
          results.push({
            operation: key.substring(PREFIX.length),
            avgDuration: Math.round(durations.reduce((a, b) => a + b, 0) / durations.length),
            maxDuration: Math.max(...durations),
            count: durations.length,
          })
        }
      } catch {}
    }
    return results.sort((a, b) => b.avgDuration - a.avgDuration)
  },

  getPerformanceSummary(): { totalOperations: number; avgDuration: number; slowOperations: number; failureRate: number } {
    const keys = Object.keys(localStorage).filter(k => k.startsWith(PREFIX))
    let totalOps = 0; let totalDuration = 0; let slowOps = 0; let failures = 0
    for (const key of keys) {
      try {
        const samples = JSON.parse(localStorage.getItem(key) || '[]') as PerformanceSample[]
        totalOps += samples.length
        for (const s of samples) {
          totalDuration += s.duration
          if (s.duration > 5000) slowOps++
          if (!s.success) failures++
        }
      } catch {}
    }
    return {
      totalOperations: totalOps,
      avgDuration: totalOps > 0 ? Math.round(totalDuration / totalOps) : 0,
      slowOperations: slowOps,
      failureRate: totalOps > 0 ? Math.round((failures / totalOps) * 100) : 0,
    }
  },

  clearHistory(operation?: string): void {
    if (operation) {
      localStorage.removeItem(PREFIX + operation)
    } else {
      const keys = Object.keys(localStorage).filter(k => k.startsWith(PREFIX))
      for (const key of keys) localStorage.removeItem(key)
    }
  },
}
