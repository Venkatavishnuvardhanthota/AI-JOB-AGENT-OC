import type { MetricSample, MetricSeries, ServiceName } from './production-types'
import { nowISO } from '../orchestration/utils'

const PREFIX = 'ajapp_met_'
const MAX_SAMPLES_PER_METRIC = 10000

function get<T>(key: string, fallback: T): T {
  try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback } catch { return fallback }
}
function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

function metricKey(name: string, tags: Record<string, string>): string {
  return `${name}:${Object.entries(tags).sort(([a], [b]) => a.localeCompare(b)).map(([k, v]) => `${k}=${v}`).join(',')}`
}

export const metricsService = {
  record(name: string, value: number, unit: MetricSample['unit'] = 'count', tags: Record<string, string> = {}, service: ServiceName = 'analytics'): MetricSample {
    const sample: MetricSample = { name, value, unit, tags, service, timestamp: nowISO() }
    const key = metricKey(name, tags)
    const series = this.getSeries(name, tags)
    series.push(sample)
    if (series.length > MAX_SAMPLES_PER_METRIC) series.splice(0, series.length - MAX_SAMPLES_PER_METRIC)
    set(PREFIX + key, series)
    return sample
  },

  getSeries(name: string, tags: Record<string, string> = {}): MetricSample[] {
    return get<MetricSample[]>(PREFIX + metricKey(name, tags), [])
  },

  getAggregatedSeries(name: string): MetricSeries[] {
    const keys = Object.keys(localStorage).filter(k => k.startsWith(PREFIX + name + ':'))
    return keys.map(key => {
      const samples = get<MetricSample[]>(key, [])
      const first = samples[0]
      if (!first) return null
      return {
        name: first.name,
        unit: first.unit,
        samples: samples.map(s => ({ timestamp: s.timestamp, value: s.value })),
        tags: first.tags,
        service: first.service,
      }
    }).filter((s): s is MetricSeries => s !== null)
  },

  getCurrentValue(name: string, tags: Record<string, string> = {}): number | null {
    const series = this.getSeries(name, tags)
    return series.length > 0 ? series[series.length - 1].value : null
  },

  getAggregatedValue(name: string, tags: Record<string, string> = {}, aggregation: 'avg' | 'sum' | 'min' | 'max' | 'count' = 'avg'): number {
    const samples = this.getSeries(name, tags)
    if (samples.length === 0) return 0
    const recent = samples.slice(-100)
    const values = recent.map(s => s.value)
    switch (aggregation) {
      case 'sum': return values.reduce((a, b) => a + b, 0)
      case 'avg': return Math.round(values.reduce((a, b) => a + b, 0) / values.length)
      case 'min': return Math.min(...values)
      case 'max': return Math.max(...values)
      case 'count': return values.length
    }
  },

  increment(name: string, tags: Record<string, string> = {}, service: ServiceName = 'analytics'): void {
    const current = this.getCurrentValue(name, tags) ?? 0
    this.record(name, current + 1, 'count', tags, service)
  },

  recordDuration(name: string, durationMs: number, tags: Record<string, string> = {}, service?: ServiceName): void {
    this.record(name, durationMs, 'ms', tags, service ?? 'analytics')
  },

  getAllMetricNames(): string[] {
    const names = new Set<string>()
    const keys = Object.keys(localStorage).filter(k => k.startsWith(PREFIX))
    for (const key of keys) {
      const name = key.substring(PREFIX.length).split(':')[0]
      names.add(name)
    }
    return Array.from(names).sort()
  },

  getMetricsSummary(service?: ServiceName): { name: string; current: number; unit: string; avg: number; min: number; max: number }[] {
    const names = this.getAllMetricNames()
    return names.map(name => {
      const series = this.getAggregatedSeries(name)
      const samples = series.flatMap(s => s.samples.map(ss => ss.value))
      const first = series[0]
      if (!first || (service && first.service !== service)) return null
      return {
        name,
        current: samples[samples.length - 1] ?? 0,
        unit: first.unit,
        avg: samples.length > 0 ? Math.round(samples.reduce((a, b) => a + b, 0) / samples.length) : 0,
        min: samples.length > 0 ? Math.min(...samples) : 0,
        max: samples.length > 0 ? Math.max(...samples) : 0,
      }
    }).filter((s): s is NonNullable<typeof s> => s !== null)
  },

  clear(): void {
    const keys = Object.keys(localStorage).filter(k => k.startsWith(PREFIX))
    for (const key of keys) localStorage.removeItem(key)
  },
}

export function recordJobDiscovered(tags?: Record<string, string>): void {
  metricsService.increment('jobs.discovered', tags, 'discovery-engine')
}

export function recordJobMatched(tags?: Record<string, string>): void {
  metricsService.increment('jobs.matched', tags, 'matching-engine')
}

export function recordPackageGenerated(tags?: Record<string, string>): void {
  metricsService.increment('packages.generated', tags, 'generation-engine')
}

export function recordBrowserSession(tags?: Record<string, string>): void {
  metricsService.increment('browser.sessions', tags, 'browser-framework')
}

export function recordWorkflowExecution(tags?: Record<string, string>): void {
  metricsService.increment('workflow.executions', tags, 'workflow-engine')
}

export function recordsQueueThroughput(tags?: Record<string, string>): void {
  metricsService.increment('queue.throughput', tags, 'workflow-engine')
}

export function recordRetry(tags?: Record<string, string>): void {
  metricsService.increment('workflow.retries', tags, 'workflow-engine')
}

export function recordFailure(tags?: Record<string, string>): void {
  metricsService.increment('workflow.failures', tags, 'workflow-engine')
}

export function recordRecovery(tags?: Record<string, string>): void {
  metricsService.increment('workflow.recoveries', tags, 'workflow-engine')
}

export function recordProviderLatency(provider: string, latencyMs: number): void {
  metricsService.recordDuration('provider.latency', latencyMs, { provider }, 'discovery-engine')
}

export function recordExecutionTime(operation: string, durationMs: number, service?: ServiceName): void {
  metricsService.recordDuration(`execution.${operation}`, durationMs, {}, service ?? 'workflow-engine')
}
