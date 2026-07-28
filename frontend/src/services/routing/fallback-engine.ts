import type { ProviderId, SearchParams, DiscoveryError } from '../discovery/types'
import type { ProviderExecutionPlan, RoutingPolicy } from './routing-types'
import { providerRegistry } from '../discovery/provider-registry'
import { loggingService } from '../production/logging-service'

interface FallbackAttempt {
  providerId: ProviderId
  attempt: number
  success: boolean
  error: string | null
}

export interface FallbackResult {
  jobs: import('../discovery/types').RawJob[]
  errors: DiscoveryError[]
  retries: { providerId: ProviderId; attempts: number }[]
  attempts: FallbackAttempt[]
}

export async function executeFallback(
  failedProviderId: ProviderId,
  params: SearchParams,
  plan: ProviderExecutionPlan,
  policy: RoutingPolicy
): Promise<FallbackResult> {
  const errors: DiscoveryError[] = []
  const retries: { providerId: ProviderId; attempts: number }[] = []
  const attempts: FallbackAttempt[] = []
  let jobs: import('../discovery/types').RawJob[] = []

  if (policy.fallbackPolicy === 'retry' || policy.retryOnFailure) {
    const maxRetries = policy.maxRetries
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const provider = providerRegistry.get(failedProviderId)
        if (!provider) {
          attempts.push({ providerId: failedProviderId, attempt, success: false, error: 'Provider not found' })
          break
        }

        const result = await provider.search(params)
        if (!result.error) {
          jobs = result.jobs
          attempts.push({ providerId: failedProviderId, attempt, success: true, error: null })
          retries.push({ providerId: failedProviderId, attempts: attempt })
          return { jobs, errors, retries, attempts }
        }

        attempts.push({ providerId: failedProviderId, attempt, success: false, error: result.error })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error'
        attempts.push({ providerId: failedProviderId, attempt, success: false, error: message })
      }
    }

    errors.push({
      provider: failedProviderId,
      message: `Failed after ${maxRetries} retries`,
      code: 'RETRY_EXHAUSTED',
    })
  }

  if (policy.fallbackPolicy === 'switch_provider') {
    const fallbackProviders = plan.fallbackOrder.filter(
      d => d.providerId !== failedProviderId && d.action === 'fallback'
    )

    for (const fallback of fallbackProviders) {
      try {
        const provider = providerRegistry.get(fallback.providerId)
        if (!provider) continue

        const result = await provider.search(params)
        if (!result.error && result.jobs.length > 0) {
          jobs = result.jobs
          retries.push({ providerId: fallback.providerId, attempts: 1 })
          return { jobs, errors, retries, attempts }
        }
      } catch {
        continue
      }
    }

    errors.push({
      provider: failedProviderId,
      message: 'Fallback providers exhausted',
      code: 'FALLBACK_EXHAUSTED',
    })
  }

  if (policy.fallbackPolicy === 'reduce_concurrency') {
    loggingService.warn(`[routing] Reducing concurrency after ${failedProviderId} failure`, undefined, {
      providerId: failedProviderId,
    })
  }

  return { jobs, errors, retries, attempts }
}
