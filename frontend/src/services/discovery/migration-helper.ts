import type { JobProvider, ProviderId, ProviderHealth, ProviderCapability, SearchParams, SearchResult } from './types'
import type { CreatedProvider } from '../provider-sdk/provider-factory'
import type { ProviderHealthCheckResult } from '../provider-sdk/types'
import { providerRegistry as sdkRegistry } from '../provider-sdk/provider-registry'

function mapHealth(sdkHealth: ProviderHealthCheckResult): ProviderHealth {
  const now = new Date().toISOString()
  const statusMap: Record<string, ProviderHealth['status']> = {
    healthy: 'healthy', degraded: 'degraded', unhealthy: 'unhealthy',
  }
  const status = statusMap[sdkHealth.status] ?? 'healthy'
  return {
    status,
    lastSuccess: status === 'healthy' ? sdkHealth.lastCheck : now,
    lastFailure: status === 'unhealthy' ? sdkHealth.lastCheck : null,
    successRate: status === 'healthy' ? 0.95 : status === 'degraded' ? 0.7 : 0.3,
    averageLatency: sdkHealth.latency,
    errorCount: 0,
    availability: status === 'healthy' ? 0.98 : status === 'degraded' ? 0.8 : 0.5,
    consecutiveFailures: status === 'unhealthy' ? 5 : status === 'degraded' ? 3 : 0,
    lastError: null,
  }
}

const SDK_CAPABILITIES_MAP: Record<string, ProviderCapability> = {
  search: 'search',
  filter_by_location: 'filter_by_location',
  filter_by_salary: 'filter_by_salary',
  filter_by_experience: 'filter_by_experience',
  filter_by_type: 'filter_by_type',
  easy_apply: 'easy_apply',
  company_profile: 'company_profile',
  salary_range: 'salary_range',
}

function mapCapabilities(sdkCaps: string[]): ProviderCapability[] {
  return sdkCaps.filter(c => SDK_CAPABILITIES_MAP[c]).map(c => SDK_CAPABILITIES_MAP[c])
}

export function toJobProvider(created: CreatedProvider): JobProvider {
  const config = created.getConfig()
  const providerCapabilities = mapCapabilities(created.metadata.capabilities)

  const provider: JobProvider = {
    id: created.metadata.id as ProviderId,
    name: created.metadata.name,
    enabled: config?.enabled ?? true,
    priority: config?.priority ?? 100,
    capabilities: providerCapabilities,

    async search(params: SearchParams): Promise<SearchResult> {
      return created.search(params)
    },

    async health(): Promise<ProviderHealth> {
      const h = await created.health()
      return mapHealth(h)
    },
  }

  return provider
}

export function createDiscoveryProvider(
  sdkProvider: CreatedProvider,
  sdkCapabilities: string[],
  priority: number
): JobProvider {
  const result = toJobProvider(sdkProvider)
  result.priority = priority
  result.capabilities = sdkCapabilities.filter(c => SDK_CAPABILITIES_MAP[c]).map(c => SDK_CAPABILITIES_MAP[c])
  try { sdkRegistry.register(sdkProvider.metadata, sdkProvider, sdkProvider.getConfig()) } catch {}
  return result
}
