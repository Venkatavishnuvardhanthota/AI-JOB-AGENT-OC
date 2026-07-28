import type {
  ProviderId, SearchParams, ProviderCapability, ProviderHealth,
  DiscoveryResult,
} from '../discovery/types'

export interface ProviderMetadata {
  id: ProviderId
  name: string
  version: string
  region: string[]
  country: string[]
  jobTypes: string[]
  supportsInternships: boolean
  supportsFreshers: boolean
  supportsRemote: boolean
  authenticationRequired: boolean
  estimatedLatency: number
  reliabilityScore: number
  priority: number
  capabilitySupport: ProviderCapability[]
  featureSupport: string[]
  lastSuccessfulHealthCheck: string | null
}

export interface RoutingContext {
  searchParams: SearchParams
  correlationId: string
  requestId: string
  timestamp: number
}

export interface ProviderRoutingDecision {
  providerId: ProviderId
  action: 'include' | 'skip' | 'fallback'
  reason: string
  priority: number
  metadata: ProviderMetadata | null
  health: ProviderHealth | null
}

export interface ProviderExecutionPlan {
  correlationId: string
  decisions: ProviderRoutingDecision[]
  parallelGroups: ProviderRoutingDecision[][]
  fallbackOrder: ProviderRoutingDecision[]
  timeout: number
  maxConcurrency: number
}

export interface RoutingPolicy {
  enabled: boolean
  preferRegion: string[]
  excludeRegion: string[]
  preferJobTypes: string[]
  maxConcurrency: number
  timeout: number
  retryOnFailure: boolean
  maxRetries: number
  enableHealthAware: boolean
  enableFallback: boolean
  enableDuplicateResolution: boolean
  fallbackPolicy: 'retry' | 'switch_provider' | 'reduce_concurrency' | 'skip' | 'escalate'
}

export interface RoutingConfiguration {
  preferredProviders: ProviderId[]
  excludedProviders: ProviderId[]
  regionFilters: string[]
  priorityOverrides: Record<string, number>
  concurrency: number
  timeout: number
  fallbackPolicy: RoutingPolicy['fallbackPolicy']
}

export interface SearchAnalytics {
  correlationId: string
  totalProviders: number
  providersSearched: number
  providersSkipped: number
  providersFailed: number
  providersFallback: number
  executionTime: number
  jobsFound: number
  duplicatesRemoved: number
  uniqueJobs: number
  failures: { providerId: ProviderId; error: string; code: string }[]
  retries: { providerId: ProviderId; attempts: number }[]
  individualLatencies: { providerId: ProviderId; latency: number; success: boolean }[]
  averageLatency: number
  successRate: number
}

export interface RoutingResult {
  discoveryResult: DiscoveryResult
  analytics: SearchAnalytics
}

export interface SearchAnalyticsStore {
  history: SearchAnalytics[]
  summary: {
    totalSearches: number
    totalJobsFound: number
    totalDuplicatesRemoved: number
    averageExecutionTime: number
    averageLatency: number
    overallSuccessRate: number
    topProvidersByUsage: { providerId: ProviderId; count: number }[]
    topProvidersByFailure: { providerId: ProviderId; count: number }[]
  }
}

export const DEFAULT_ROUTING_POLICY: RoutingPolicy = {
  enabled: true,
  preferRegion: [],
  excludeRegion: [],
  preferJobTypes: [],
  maxConcurrency: 5,
  timeout: 30000,
  retryOnFailure: true,
  maxRetries: 2,
  enableHealthAware: true,
  enableFallback: true,
  enableDuplicateResolution: true,
  fallbackPolicy: 'retry',
}

export const DEFAULT_ROUTING_CONFIGURATION: RoutingConfiguration = {
  preferredProviders: [],
  excludedProviders: [],
  regionFilters: [],
  priorityOverrides: {},
  concurrency: 5,
  timeout: 30000,
  fallbackPolicy: 'retry',
}
