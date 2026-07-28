import type { ProviderId, SearchParams, DiscoveryError } from '../discovery/types'
import type { ProviderRoutingDecision, ProviderExecutionPlan } from './routing-types'
import { providerRegistry } from '../discovery/provider-registry'

interface ProviderResult {
  providerId: ProviderId
  jobs: import('../discovery/types').RawJob[]
  duration: number
  error: string | null
  errorCode: string | null
}

export async function executePlan(
  plan: ProviderExecutionPlan,
  params: SearchParams
): Promise<{ results: ProviderResult[]; errors: DiscoveryError[]; latencies: { providerId: ProviderId; latency: number; success: boolean }[] }> {
  const allResults: ProviderResult[] = []
  const allErrors: DiscoveryError[] = []
  const allLatencies: { providerId: ProviderId; latency: number; success: boolean }[] = []

  const ac = new AbortController()
  const timeout = plan.timeout

  const timeoutId = setTimeout(() => ac.abort(), timeout)

  try {
    const included = plan.decisions.filter(d => d.action === 'include' || d.action === 'fallback')

    const groups = createParallelGroups(included, plan.maxConcurrency)

    for (const group of groups) {
      if (ac.signal.aborted) break

      const groupPromises = group.map(decision =>
        executeProviderSearch(decision.providerId, params, plan)
          .then(result => {
            allResults.push(result)
            allLatencies.push({
              providerId: result.providerId,
              latency: result.duration,
              success: result.error === null,
            })
            if (result.error) {
              allErrors.push({
                provider: result.providerId,
                message: result.error,
                code: result.errorCode ?? 'PROVIDER_ERROR',
              })
            }
            return result
          })
      )

      await Promise.allSettled(groupPromises)
    }
  } finally {
    clearTimeout(timeoutId)
  }

  return { results: allResults, errors: allErrors, latencies: allLatencies }
}

function createParallelGroups(
  decisions: ProviderRoutingDecision[],
  maxConcurrency: number
): ProviderRoutingDecision[][] {
  const groups: ProviderRoutingDecision[][] = []
  for (let i = 0; i < decisions.length; i += maxConcurrency) {
    groups.push(decisions.slice(i, i + maxConcurrency))
  }
  if (groups.length === 0) groups.push([])
  return groups
}

async function executeProviderSearch(
  providerId: ProviderId,
  params: SearchParams,
  _plan: ProviderExecutionPlan
): Promise<ProviderResult> {
  const start = Date.now()

  try {
    const provider = providerRegistry.get(providerId)
    if (!provider) {
      return { providerId, jobs: [], duration: Date.now() - start, error: 'Provider not found in registry', errorCode: 'PROVIDER_NOT_FOUND' }
    }

    const result = await provider.search(params)
    const duration = Date.now() - start

    if (result.error) {
      return { providerId, jobs: [], duration, error: result.error, errorCode: 'SEARCH_ERROR' }
    }

    return { providerId, jobs: result.jobs, duration, error: null, errorCode: null }
  } catch (err) {
    const duration = Date.now() - start
    const message = err instanceof Error ? err.message : 'Unknown error'
    return { providerId, jobs: [], duration, error: message, errorCode: 'PROVIDER_ERROR' }
  }
}
