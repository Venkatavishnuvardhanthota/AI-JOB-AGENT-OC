import type { SearchParams } from '../discovery/types'
import type { ProviderRoutingDecision, RoutingConfiguration } from './routing-types'

export function rankProviders(
  decisions: ProviderRoutingDecision[],
  params: SearchParams,
  config?: RoutingConfiguration
): ProviderRoutingDecision[] {
  const originalPriorities = new Map(decisions.map(d => [d.providerId, d.priority]))

  return decisions
    .map(d => {
      let score = 0
      const meta = d.metadata
      const health = d.health

      const effectivePriority = config?.priorityOverrides?.[d.providerId] ?? meta?.priority ?? 100
      score += Math.max(0, 100 - effectivePriority) * 2

      if (health) {
        score += health.successRate * 10
        score += health.availability * 8
        score += Math.max(0, 1 - (health.averageLatency / 10000)) * 5
        if (health.status === 'healthy') score += 8
        else if (health.status === 'degraded') score += 3
      }

      if (meta) {
        score += meta.reliabilityScore * 10

        if (params.location && meta.country.some(c => params.location!.toLowerCase().includes(c))) {
          score += 6
        }
        if (params.employmentType === 'internship' && meta.supportsInternships) {
          score += 6
        }
        if ((params.experienceLevel === 'entry' || params.experienceLevel === 'internship') && meta.supportsFreshers) {
          score += 6
        }
        if (params.remote === 'remote' && meta.supportsRemote) {
          score += 5
        }
      }

      if (config?.preferredProviders?.includes(d.providerId)) {
        score += 20
      }
      if (config?.excludedProviders?.includes(d.providerId)) {
        score -= 100
      }

      return { ...d, priority: Math.max(0, 100 - Math.round(score)) }
    })
    .filter(d => {
      if (config?.excludedProviders?.includes(d.providerId)) return false
      return true
    })
    .sort((a, b) => {
      if (a.priority !== b.priority) return a.priority - b.priority
      const origA = originalPriorities.get(a.providerId) ?? 100
      const origB = originalPriorities.get(b.providerId) ?? 100
      return origA - origB
    })
}
