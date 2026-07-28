import type { ProviderId, ProviderHealth } from '../discovery/types'
import { providerHealthService } from '../discovery/provider-health'
import type { ProviderRoutingDecision } from './routing-types'
import { providerMetadataService } from './provider-metadata'
import { providerRegistry } from '../discovery/provider-registry'

const DEGRADED_CONSECUTIVE_FAILURES = 3
const UNHEALTHY_CONSECUTIVE_FAILURES = 5
const MAX_ACCEPTABLE_LATENCY = 10000
const MIN_ACCEPTABLE_SUCCESS_RATE = 0.3
const MIN_ACCEPTABLE_AVAILABILITY = 0.3

export const healthAwareRouter = {
  isHealthy(id: ProviderId): boolean {
    const health = providerHealthService.get(id)
    return health.status === 'healthy'
  },

  isAvailable(id: ProviderId): boolean {
    const health = providerHealthService.get(id)
    if (health.status === 'disabled') return false
    if (health.status === 'unhealthy') {
      if (health.consecutiveFailures >= UNHEALTHY_CONSECUTIVE_FAILURES) return false
    }
    return true
  },

  getHealthStatus(id: ProviderId): ProviderHealth {
    return providerHealthService.get(id)
  },

  evaluate(providerIds: ProviderId[]): ProviderRoutingDecision[] {
    return providerIds.map(id => {
      const provider = providerRegistry.get(id)
      if (!provider || !provider.enabled) {
        return {
          providerId: id,
          action: 'skip',
          reason: 'Provider is disabled in registry',
          priority: 999,
          metadata: providerMetadataService.get(id),
          health: providerHealthService.get(id),
        }
      }

      const health = providerHealthService.get(id)
      const meta = providerMetadataService.get(id)
      let action: ProviderRoutingDecision['action'] = 'include'
      const reasons: string[] = []

      if (health.status === 'disabled') {
        action = 'skip'
        reasons.push('Provider is disabled')
      } else if (health.status === 'unhealthy') {
        if (health.consecutiveFailures >= UNHEALTHY_CONSECUTIVE_FAILURES) {
          action = 'skip'
          reasons.push(`Unhealthy (${health.consecutiveFailures} consecutive failures)`)
        } else {
          action = 'fallback'
          reasons.push(`Degraded health (${health.consecutiveFailures} failures)`)
        }
      } else if (health.status === 'degraded') {
        if (health.consecutiveFailures >= DEGRADED_CONSECUTIVE_FAILURES) {
          action = 'fallback'
          reasons.push(`${health.consecutiveFailures} consecutive failures`)
        } else {
          action = 'include'
          reasons.push('Minor degradation')
        }
      }

      if (action === 'include' && health.averageLatency > MAX_ACCEPTABLE_LATENCY) {
        reasons.push(`High latency (${health.averageLatency}ms)`)
      }

      if (health.successRate < MIN_ACCEPTABLE_SUCCESS_RATE) {
        if (action === 'include') {
          action = 'fallback'
        }
        reasons.push(`Low success rate (${(health.successRate * 100).toFixed(0)}%)`)
      }

      if (health.availability < MIN_ACCEPTABLE_AVAILABILITY) {
        if (action === 'include') {
          action = 'fallback'
        }
        reasons.push(`Low availability (${(health.availability * 100).toFixed(0)}%)`)
      }

      return {
        providerId: id,
        action,
        reason: reasons.join('; ') || 'Healthy',
        priority: meta.priority,
        metadata: meta,
        health,
      }
    })
  },
}
