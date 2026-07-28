import type { ProviderId, ProviderHealth, SearchResult } from '../discovery/types'
import type { ManagedProvider, ProviderFilterOptions, ProviderDetails, BulkActionResult, DiscoveryConfiguration } from './provider-management-types'
import { DEFAULT_DISCOVERY_CONFIG } from './provider-management-types'
import { providerRegistry } from '../discovery/provider-registry'
import { providerHealthService } from '../discovery/provider-health'
import { providerMetadataService } from '../routing/provider-metadata'
import { categorizeProvider, getCategories } from './provider-categories'
import { searchAnalyticsService } from '../routing/search-analytics'
import { loggingService } from '../production/logging-service'

const CONFIG_PREFIX = 'ajapp_disc_config_'

function getConfig(): DiscoveryConfiguration {
  try {
    const raw = localStorage.getItem(CONFIG_PREFIX + 'discovery')
    return raw ? { ...DEFAULT_DISCOVERY_CONFIG, ...JSON.parse(raw) } : DEFAULT_DISCOVERY_CONFIG
  } catch {
    return DEFAULT_DISCOVERY_CONFIG
  }
}

function setConfig(config: DiscoveryConfiguration): void {
  try { localStorage.setItem(CONFIG_PREFIX + 'discovery', JSON.stringify(config)) } catch {}
}

const jobsTodayCache = new Map<ProviderId, number>()

export const providerManagementService = {
  getProviders(): ManagedProvider[] {
    const providers = providerRegistry.getAll()
    const allHealth = providerHealthService.getAll()

    return providers.map(p => {
      const metadata = providerMetadataService.get(p.id)
      const health = allHealth[p.id] ?? providerHealthService.get(p.id)
      const config = providerRegistry.getConfigs().find(c => c.id === p.id) ?? {
        id: p.id, name: p.name, enabled: p.enabled, priority: p.priority,
        capabilities: p.capabilities, baseUrl: null, apiKeyRequired: false, apiKeyConfigured: false,
      }

      return {
        id: p.id,
        name: p.name,
        category: categorizeProvider(metadata),
        description: metadata.name,
        version: metadata.version,
        enabled: p.enabled,
        priority: p.priority,
        metadata,
        health,
        config,
        lastSearchTime: health.lastSuccess,
        jobsFoundToday: jobsTodayCache.get(p.id) ?? 0,
      }
    })
  },

  getCategories(providers?: ManagedProvider[]) {
    const target = providers ?? this.getProviders()
    return getCategories(target)
  },

  getFilteredProviders(filters: ProviderFilterOptions): ManagedProvider[] {
    let providers = this.getProviders()

    if (filters.search) {
      const q = filters.search.toLowerCase()
      providers = providers.filter(p =>
        p.name.toLowerCase().includes(q) || p.id.toLowerCase().includes(q)
      )
    }

    if (filters.categories.length > 0) {
      providers = providers.filter(p => filters.categories.includes(p.category))
    }

    if (filters.regions.length > 0) {
      providers = providers.filter(p =>
        p.metadata.region.some(r => filters.regions.includes(r))
      )
    }

    if (filters.countries.length > 0) {
      providers = providers.filter(p =>
        p.metadata.country.some(c => filters.countries.includes(c))
      )
    }

    if (filters.healthStatuses.length > 0) {
      providers = providers.filter(p =>
        filters.healthStatuses.includes(p.health.status)
      )
    }

    if (filters.capabilities.length > 0) {
      providers = providers.filter(p =>
        filters.capabilities.every(c => p.metadata.capabilitySupport.includes(c))
      )
    }

    if (filters.enabled !== null) {
      providers = providers.filter(p => p.enabled === filters.enabled)
    }

    providers.sort((a, b) => {
      let cmp = 0
      switch (filters.sortBy) {
        case 'name':
          cmp = a.name.localeCompare(b.name)
          break
        case 'priority':
          cmp = a.priority - b.priority
          break
        case 'latency':
          cmp = a.health.averageLatency - b.health.averageLatency
          break
        case 'reliability':
          cmp = a.metadata.reliabilityScore - b.metadata.reliabilityScore
          break
        case 'health':
          const order = ['healthy', 'warning', 'degraded', 'unhealthy', 'disabled']
          cmp = order.indexOf(a.health.status) - order.indexOf(b.health.status)
          break
      }
      return filters.sortOrder === 'desc' ? -cmp : cmp
    })

    return providers
  },

  enableProvider(id: ProviderId): void {
    providerRegistry.enable(id)
  },

  disableProvider(id: ProviderId): void {
    providerRegistry.disable(id)
  },

  async runHealthCheck(id: ProviderId): Promise<ProviderHealth> {
    const provider = providerRegistry.get(id)
    if (!provider) throw new Error(`Provider not found: ${id}`)
    try {
      const health = await provider.health()
      return health
    } catch {
      return {
        status: 'unhealthy', lastSuccess: null, lastFailure: new Date().toISOString(),
        successRate: 0, averageLatency: 0, errorCount: 1, availability: 0,
        consecutiveFailures: 1, lastError: 'Health check failed',
      }
    }
  },

  async testSearch(id: ProviderId): Promise<SearchResult | { error: string }> {
    const provider = providerRegistry.get(id)
    if (!provider) return { error: `Provider not found: ${id}` }
    try {
      return await provider.search({
        keywords: 'software engineer', location: null, remote: null,
        salaryMin: null, salaryMax: null, experienceLevel: null,
        employmentType: null, postedWithinDays: null, easyApplyOnly: false,
        page: 1, pageSize: 5,
      })
    } catch (err) {
      return { error: err instanceof Error ? err.message : 'Search failed' }
    }
  },

  bulkAction(action: 'enable' | 'disable', ids: ProviderId[]): BulkActionResult {
    const result: BulkActionResult = { success: 0, failed: 0, errors: [] }
    for (const id of ids) {
      try {
        if (action === 'enable') providerRegistry.enable(id)
        else providerRegistry.disable(id)
        result.success++
      } catch (err) {
        result.failed++
        result.errors.push({ providerId: id, error: err instanceof Error ? err.message : 'Unknown error' })
      }
    }
    return result
  },

  getConfiguration(): DiscoveryConfiguration {
    return getConfig()
  },

  saveConfiguration(config: DiscoveryConfiguration): void {
    setConfig(config)
  },

  getProviderDetails(id: ProviderId): ProviderDetails {
    const provider = this.getProviders().find(p => p.id === id)
    if (!provider) throw new Error(`Provider not found: ${id}`)

    const analyticsHistory = searchAnalyticsService.getHistory()
    const providerAnalytics = analyticsHistory.filter(a =>
      a.individualLatencies.some(l => l.providerId === id)
    )

    const recentSearches = providerAnalytics.slice(0, 10).map(a => ({
      query: a.correlationId,
      timestamp: new Date().toISOString(),
      jobsFound: a.jobsFound,
    }))

    const latencies = providerAnalytics.flatMap(a =>
      a.individualLatencies.filter(l => l.providerId === id)
    )
    const successLatencies = latencies.filter(l => l.success)

    const searchCount = latencies.length
    const successCount = successLatencies.length
    const averageLatency = successLatencies.length > 0
      ? Math.round(successLatencies.reduce((s, l) => s + l.latency, 0) / successLatencies.length)
      : 0
    const successRate = searchCount > 0 ? successCount / searchCount : 0

    return {
      provider,
      recentSearches,
      metrics: {
        averageLatency,
        successRate,
        failureRate: 1 - successRate,
        retryCount: providerAnalytics.reduce((s, a) => s + a.retries.filter(r => r.providerId === id).length, 0),
        lastError: provider.health.lastError,
        searchCount,
        jobsReturned: providerAnalytics.reduce((s, a) => s + a.jobsFound, 0),
      },
      logs: loggingService.getByCorrelationId(id).slice(0, 50).map(e => ({
        timestamp: e.timestamp,
        level: e.level,
        message: e.message,
      })),
    }
  },

  resetProvider(id: ProviderId): void {
    providerHealthService.reset(id)
    loggingService.info(`[provider-management] Provider reset: ${id}`, { correlationId: id }, { providerId: id })
  },
}
