import type { ProviderHealth, ProviderId, ProviderStatus } from './types'
import { providerRegistry } from './provider-registry'

const PREFIX = 'ajapp_disc_health_'

function get<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch { return fallback }
}

function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

const DEFAULT_HEALTH: ProviderHealth = {
  status: 'healthy',
  lastSuccess: null,
  lastFailure: null,
  successRate: 1.0,
  averageLatency: 0,
  errorCount: 0,
  availability: 1.0,
  consecutiveFailures: 0,
  lastError: null,
}

export const providerHealthService = {
  get(id: ProviderId): ProviderHealth {
    return get<ProviderHealth>(`${PREFIX}${id}`, DEFAULT_HEALTH)
  },

  getAll(): Record<ProviderId, ProviderHealth> {
    const result: Record<string, ProviderHealth> = {}
    for (const provider of providerRegistry.getAll()) {
      result[provider.id] = this.get(provider.id)
    }
    return result as Record<ProviderId, ProviderHealth>
  },

  recordSuccess(id: ProviderId, latency: number): void {
    const health = this.get(id)
    const newHealth: ProviderHealth = {
      ...health,
      status: 'healthy',
      lastSuccess: new Date().toISOString(),
      averageLatency: health.averageLatency === 0
        ? latency
        : Math.round((health.averageLatency * 0.7 + latency * 0.3)),
      errorCount: 0,
      consecutiveFailures: 0,
      lastError: null,
      availability: Math.min(1, health.availability + 0.01),
      successRate: Math.min(1, health.successRate + 0.005),
    }
    set(`${PREFIX}${id}`, newHealth)
  },

  recordFailure(id: ProviderId, error: string, latency?: number): void {
    const health = this.get(id)
    const consecutiveFailures = health.consecutiveFailures + 1
    let status: ProviderStatus = 'healthy'
    if (consecutiveFailures >= 5) status = 'unhealthy'
    else if (consecutiveFailures >= 3) status = 'degraded'

    const newHealth: ProviderHealth = {
      ...health,
      status,
      lastFailure: new Date().toISOString(),
      lastError: error,
      errorCount: health.errorCount + 1,
      consecutiveFailures,
      availability: Math.max(0, health.availability - 0.05),
      successRate: Math.max(0, health.successRate - 0.02),
    }
    if (latency !== undefined) {
      newHealth.averageLatency = health.averageLatency === 0
        ? latency
        : Math.round((health.averageLatency * 0.7 + latency * 0.3))
    }
    set(`${PREFIX}${id}`, newHealth)
  },

  async checkAll(): Promise<Record<ProviderId, ProviderHealth>> {
    const results: Record<string, ProviderHealth> = {}
    const providers = providerRegistry.getEnabled()
    const checks = providers.map(async (p) => {
      try {
        const health = await p.health()
        results[p.id] = health
      } catch {
        results[p.id] = { ...DEFAULT_HEALTH, status: 'unhealthy', lastFailure: new Date().toISOString(), lastError: 'Health check failed' }
      }
    })
    await Promise.allSettled(checks)
    return results as Record<ProviderId, ProviderHealth>
  },

  reset(id: ProviderId): void {
    set(`${PREFIX}${id}`, DEFAULT_HEALTH)
  },

  resetAll(): void {
    for (const provider of providerRegistry.getAll()) {
      this.reset(provider.id)
    }
  },
}
