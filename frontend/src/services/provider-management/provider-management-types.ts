import type { ProviderId, ProviderCapability, ProviderHealth, ProviderConfig, ProviderStatus } from '../discovery/types'
import type { ProviderMetadata } from '../routing/routing-types'

export interface ManagedProvider {
  id: ProviderId
  name: string
  category: string
  description: string
  version: string
  enabled: boolean
  priority: number
  metadata: ProviderMetadata
  health: ProviderHealth
  config: ProviderConfig
  lastSearchTime: string | null
  jobsFoundToday: number
  backendState: string | null
}

export interface ProviderCategory {
  name: string
  providers: ManagedProvider[]
  count: number
}

export interface ProviderFilterOptions {
  search: string
  categories: string[]
  regions: string[]
  countries: string[]
  healthStatuses: ProviderStatus[]
  capabilities: ProviderCapability[]
  enabled: boolean | null
  sortBy: 'name' | 'priority' | 'latency' | 'reliability' | 'health'
  sortOrder: 'asc' | 'desc'
}

export interface ProviderDetails {
  provider: ManagedProvider
  recentSearches: { query: string; timestamp: string; jobsFound: number }[]
  metrics: {
    averageLatency: number
    successRate: number
    failureRate: number
    retryCount: number
    lastError: string | null
    searchCount: number
    jobsReturned: number
  }
  logs: { timestamp: string; level: string; message: string }[]
}

export interface BulkActionResult {
  success: number
  failed: number
  errors: { providerId: ProviderId; error: string }[]
}

export interface DiscoveryConfiguration {
  maxProviders: number
  concurrentProviders: number
  preferredProviders: ProviderId[]
  excludedProviders: ProviderId[]
  fallbackProviders: ProviderId[]
  regionalPriority: string[]
  onlyHealthyProviders: boolean
  requireAuthentication: boolean
  searchTimeout: number
  retryCount: number
}

export const DEFAULT_DISCOVERY_CONFIG: DiscoveryConfiguration = {
  maxProviders: 20,
  concurrentProviders: 5,
  preferredProviders: [],
  excludedProviders: [],
  fallbackProviders: [],
  regionalPriority: [],
  onlyHealthyProviders: false,
  requireAuthentication: false,
  searchTimeout: 30000,
  retryCount: 2,
}
