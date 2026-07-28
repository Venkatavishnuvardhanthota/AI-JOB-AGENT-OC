import type { ProviderId } from '../discovery/types'
import type { SearchAnalytics, SearchAnalyticsStore } from './routing-types'

const PREFIX = 'ajapp_route_analytics_'
const MAX_HISTORY = 500

function get<T>(key: string, fallback: T): T {
  try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback } catch { return fallback }
}
function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

function createEmptyAnalytics(correlationId: string): SearchAnalytics {
  return {
    correlationId,
    totalProviders: 0,
    providersSearched: 0,
    providersSkipped: 0,
    providersFailed: 0,
    providersFallback: 0,
    executionTime: 0,
    jobsFound: 0,
    duplicatesRemoved: 0,
    uniqueJobs: 0,
    failures: [],
    retries: [],
    individualLatencies: [],
    averageLatency: 0,
    successRate: 1,
  }
}

export const searchAnalyticsService = {
  createSession(correlationId: string): SearchAnalytics {
    return createEmptyAnalytics(correlationId)
  },

  recordProviderResult(
    analytics: SearchAnalytics,
    providerId: ProviderId,
    latency: number,
    success: boolean,
    jobsFound: number
  ): void {
    analytics.individualLatencies.push({ providerId, latency, success })
    if (success) {
      analytics.providersSearched++
      analytics.jobsFound += jobsFound
    } else {
      analytics.providersFailed++
      analytics.failures.push({ providerId, error: 'search failed', code: 'PROVIDER_ERROR' })
    }
  },

  recordSkip(analytics: SearchAnalytics, _providerId: ProviderId): void {
    analytics.providersSkipped++
  },

  recordFallback(analytics: SearchAnalytics, _providerId: ProviderId): void {
    analytics.providersFallback++
  },

  recordRetry(analytics: SearchAnalytics, providerId: ProviderId, attempts: number): void {
    analytics.retries.push({ providerId, attempts })
  },

  finalize(analytics: SearchAnalytics, executionTime: number, duplicatesRemoved: number, uniqueJobs: number): SearchAnalytics {
    analytics.executionTime = executionTime
    analytics.duplicatesRemoved = duplicatesRemoved
    analytics.uniqueJobs = uniqueJobs
    analytics.totalProviders = analytics.providersSearched + analytics.providersSkipped + analytics.providersFailed

    const latencies = analytics.individualLatencies.filter(l => l.success)
    analytics.averageLatency = latencies.length > 0
      ? Math.round(latencies.reduce((s, l) => s + l.latency, 0) / latencies.length)
      : 0

    const total = analytics.individualLatencies.length
    analytics.successRate = total > 0
      ? analytics.individualLatencies.filter(l => l.success).length / total
      : 1

    this.save(analytics)
    return analytics
  },

  save(analytics: SearchAnalytics): void {
    const history = this.getHistory()
    history.unshift(analytics)
    if (history.length > MAX_HISTORY) history.pop()
    set(PREFIX + 'history', history)
    this.rebuildSummary()
  },

  getHistory(): SearchAnalytics[] {
    return get<SearchAnalytics[]>(PREFIX + 'history', [])
  },

  getRecent(count: number = 10): SearchAnalytics[] {
    return this.getHistory().slice(0, count)
  },

  getSummary(): SearchAnalyticsStore['summary'] {
    return get<SearchAnalyticsStore['summary']>(PREFIX + 'summary', {
      totalSearches: 0,
      totalJobsFound: 0,
      totalDuplicatesRemoved: 0,
      averageExecutionTime: 0,
      averageLatency: 0,
      overallSuccessRate: 1,
      topProvidersByUsage: [],
      topProvidersByFailure: [],
    })
  },

  rebuildSummary(): void {
    const history = this.getHistory()
    if (history.length === 0) return

    const totalSearches = history.length
    const totalJobsFound = history.reduce((s, a) => s + a.jobsFound, 0)
    const totalDuplicatesRemoved = history.reduce((s, a) => s + a.duplicatesRemoved, 0)
    const averageExecutionTime = Math.round(history.reduce((s, a) => s + a.executionTime, 0) / totalSearches)
    const averageLatency = Math.round(history.reduce((s, a) => s + a.averageLatency, 0) / totalSearches)
    const overallSuccessRate = history.reduce((s, a) => s + a.successRate, 0) / totalSearches

    const usageCount = new Map<ProviderId, number>()
    const failureCount = new Map<ProviderId, number>()
    for (const a of history) {
      for (const l of a.individualLatencies) {
        usageCount.set(l.providerId, (usageCount.get(l.providerId) ?? 0) + 1)
        if (!l.success) {
          failureCount.set(l.providerId, (failureCount.get(l.providerId) ?? 0) + 1)
        }
      }
    }

    const topProvidersByUsage = [...usageCount.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([providerId, count]) => ({ providerId, count }))

    const topProvidersByFailure = [...failureCount.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([providerId, count]) => ({ providerId, count }))

    set(PREFIX + 'summary', {
      totalSearches,
      totalJobsFound,
      totalDuplicatesRemoved,
      averageExecutionTime,
      averageLatency,
      overallSuccessRate,
      topProvidersByUsage,
      topProvidersByFailure,
    })
  },

  clear(): void {
    const keys = Object.keys(localStorage).filter(k => k.startsWith(PREFIX))
    for (const key of keys) localStorage.removeItem(key)
  },
}
