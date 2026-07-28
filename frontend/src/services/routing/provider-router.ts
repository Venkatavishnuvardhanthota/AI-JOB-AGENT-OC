import type { ProviderId, SearchParams, DiscoveryResult, DiscoveryError } from '../discovery/types'
import type {
  ProviderExecutionPlan, RoutingPolicy,
  RoutingConfiguration, RoutingResult,
} from './routing-types'
import { DEFAULT_ROUTING_POLICY, DEFAULT_ROUTING_CONFIGURATION } from './routing-types'
import { providerRegistry } from '../discovery/provider-registry'
import { providerHealthService } from '../discovery/provider-health'
import { providerMetadataService } from './provider-metadata'
import { capabilityResolver } from './capability-resolver'
import { healthAwareRouter } from './health-aware-routing'
import { rankProviders } from './priority-engine'
import { executePlan } from './parallel-coordinator'
import { executeFallback } from './fallback-engine'
import { aggregateResults } from './result-aggregator'
import { searchAnalyticsService } from './search-analytics'
import { discoveryHistoryService } from '../discovery/discovery-history'

let routingCounter = 0

export const providerRouter = {
  async search(
    params: SearchParams,
    options?: { providers?: ProviderId[]; profileId?: string; policy?: Partial<RoutingPolicy>; config?: Partial<RoutingConfiguration> }
  ): Promise<RoutingResult> {
    routingCounter++
    const start = Date.now()
    const correlationId = `route_${Date.now()}_${routingCounter}`
    const resultId = `disc_${Date.now()}_${routingCounter}`

    const policy: RoutingPolicy = { ...DEFAULT_ROUTING_POLICY, ...options?.policy }
    const config: RoutingConfiguration = { ...DEFAULT_ROUTING_CONFIGURATION, ...options?.config }

    const analytics = searchAnalyticsService.createSession(correlationId)

    const candidateProviders = options?.providers
      ? providerRegistry.getAll().filter(p => options.providers!.includes(p.id))
      : providerRegistry.getEnabled()

    let candidateIds = candidateProviders.map(p => p.id)

    if (policy.enabled) {
      const byCapability = capabilityResolver.resolve(params)
      candidateIds = candidateIds.filter(id => byCapability.includes(id))
    }

    const healthDecisions = policy.enableHealthAware
      ? healthAwareRouter.evaluate(candidateIds)
      : candidateIds.map(id => {
          const meta = providerMetadataService.get(id)
          return {
            providerId: id,
            action: 'include' as const,
            reason: 'Health check disabled',
            priority: meta.priority,
            metadata: meta,
            health: providerHealthService.get(id),
          }
        })

    const rankedDecisions = rankProviders(healthDecisions, params, config)

    const includedDecisions = rankedDecisions.filter(d => d.action === 'include')
    const fallbackDecisions = rankedDecisions.filter(d => d.action === 'fallback')

    for (const d of rankedDecisions) {
      if (d.action === 'skip') {
        searchAnalyticsService.recordSkip(analytics, d.providerId)
      } else if (d.action === 'fallback') {
        searchAnalyticsService.recordFallback(analytics, d.providerId)
      }
    }

    const plan: ProviderExecutionPlan = {
      correlationId,
      decisions: rankedDecisions,
      parallelGroups: [includedDecisions],
      fallbackOrder: fallbackDecisions,
      timeout: policy.timeout,
      maxConcurrency: config.concurrency || policy.maxConcurrency,
    }

    const { results, errors: executionErrors, latencies } = await executePlan(plan, params)

    for (const lat of latencies) {
      if (lat.success) {
        providerHealthService.recordSuccess(lat.providerId, lat.latency)
        providerMetadataService.updateHealthCheck(lat.providerId, true)
      } else {
        providerHealthService.recordFailure(lat.providerId, `search failed`)
      }
      searchAnalyticsService.recordProviderResult(
        analytics, lat.providerId, lat.latency, lat.success,
        results.find(r => r.providerId === lat.providerId)?.jobs.length ?? 0
      )
    }

    const failedProviders = results.filter(r => r.error !== null).map(r => r.providerId)
    let fallbackJobs: import('../discovery/types').RawJob[] = []

    if (policy.enableFallback && failedProviders.length > 0) {
      for (const failedId of failedProviders) {
        const fallbackResult = await executeFallback(failedId, params, plan, policy)
        fallbackJobs.push(...fallbackResult.jobs)
        for (const retry of fallbackResult.retries) {
          searchAnalyticsService.recordRetry(analytics, retry.providerId, retry.attempts)
        }
        for (const attempt of fallbackResult.attempts) {
          if (attempt.success) {
            providerHealthService.recordSuccess(attempt.providerId, 0)
          }
        }
      }
    }

    const allSources = [...results.map(r => ({ providerId: r.providerId, jobs: r.jobs }))]
    if (fallbackJobs.length > 0) {
      allSources.push({ providerId: 'company_careers' as ProviderId, jobs: fallbackJobs })
    }

    const { jobs: uniqueJobs, duplicates, normalizedCount } = aggregateResults(
      allSources, rankedDecisions, params.keywords
    )

    const allErrors: DiscoveryError[] = [
      ...executionErrors,
      ...results.filter(r => r.error).map(r => ({
        provider: r.providerId,
        message: r.error!,
        code: 'PROVIDER_ERROR' as const,
      })),
    ]

    const executionTime = Date.now() - start
    const status: DiscoveryResult['status'] = allErrors.length === 0
      ? 'completed'
      : allErrors.length >= candidateProviders.length
        ? 'failed'
        : 'partial'

    const discoveryResult: DiscoveryResult = {
      id: resultId,
      query: params.keywords,
      location: params.location,
      timestamp: new Date(start).toISOString(),
      providersUsed: results.map(r => r.providerId),
      jobsFound: normalizedCount,
      duplicatesRemoved: duplicates.length,
      uniqueJobs: uniqueJobs.length,
      jobs: uniqueJobs,
      errors: allErrors,
      executionTime,
      completedAt: new Date().toISOString(),
      status,
    }

    const finalizedAnalytics = searchAnalyticsService.finalize(
      analytics, executionTime, duplicates.length, uniqueJobs.length
    )

    discoveryHistoryService.add({
      id: resultId,
      query: params.keywords,
      location: params.location,
      timestamp: discoveryResult.timestamp,
      providersUsed: discoveryResult.providersUsed,
      jobsFound: discoveryResult.jobsFound,
      duplicatesRemoved: discoveryResult.duplicatesRemoved,
      uniqueJobs: discoveryResult.uniqueJobs,
      errors: allErrors,
      executionTime,
      status,
      profileId: options?.profileId ?? null,
    })

    return { discoveryResult, analytics: finalizedAnalytics }
  },
}
