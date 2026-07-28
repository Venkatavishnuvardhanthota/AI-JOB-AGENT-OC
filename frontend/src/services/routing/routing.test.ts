import { describe, it, expect, beforeEach, vi } from 'vitest'
import { providerMetadataService } from './provider-metadata'
import { capabilityResolver } from './capability-resolver'
import { healthAwareRouter } from './health-aware-routing'
import { rankProviders } from './priority-engine'
import { aggregateResults } from './result-aggregator'
import { searchAnalyticsService } from './search-analytics'
import { providerRouter } from './provider-router'
import { DEFAULT_ROUTING_POLICY, DEFAULT_ROUTING_CONFIGURATION } from './routing-types'
import type { ProviderId, SearchParams, ProviderHealth } from '../discovery/types'

vi.mock('../discovery/provider-registry', () => ({
  providerRegistry: {
    getAll: vi.fn(),
    get: vi.fn(),
    getEnabled: vi.fn(),
    getPrioritized: vi.fn(),
    getByCapability: vi.fn(),
  },
}))

vi.mock('../discovery/provider-health', () => ({
  providerHealthService: {
    get: vi.fn(),
    recordSuccess: vi.fn(),
    recordFailure: vi.fn(),
    reset: vi.fn(),
  },
}))

vi.mock('../discovery/discovery-history', () => ({
  discoveryHistoryService: {
    add: vi.fn(),
  },
}))

import { providerRegistry } from '../discovery/provider-registry'
import { providerHealthService } from '../discovery/provider-health'

function createMockProvider(id: ProviderId, capabilities: string[] = ['search'], enabled = true, priority = 100) {
  return {
    id,
    name: id.charAt(0).toUpperCase() + id.slice(1),
    enabled,
    priority,
    capabilities,
    search: vi.fn().mockResolvedValue({ jobs: [], totalResults: 0, page: 1, pageSize: 10, hasMore: false, provider: id, duration: 0, error: null }),
    health: vi.fn().mockResolvedValue({ status: 'healthy', lastSuccess: null, lastFailure: null, successRate: 1, averageLatency: 0, errorCount: 0, availability: 1, consecutiveFailures: 0, lastError: null }),
  }
}

const defaultHealth: ProviderHealth = {
  status: 'healthy', lastSuccess: new Date().toISOString(), lastFailure: null,
  successRate: 0.95, averageLatency: 500, errorCount: 0, availability: 0.98,
  consecutiveFailures: 0, lastError: null,
}

function makeSearchParams(overrides?: Partial<SearchParams>): SearchParams {
  return {
    keywords: 'software engineer',
    location: null,
    remote: null,
    salaryMin: null,
    salaryMax: null,
    experienceLevel: null,
    employmentType: null,
    postedWithinDays: null,
    easyApplyOnly: false,
    page: 1,
    pageSize: 10,
    ...overrides,
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  searchAnalyticsService.clear()
; (providerRegistry.getEnabled as any).mockReturnValue([
    createMockProvider('linkedin', ['search', 'filter_by_location', 'filter_by_experience', 'easy_apply', 'company_profile', 'salary_range'], true, 1),
    createMockProvider('indeed', ['search', 'filter_by_location', 'filter_by_salary', 'easy_apply'], true, 2),
    createMockProvider('naukri', ['search', 'filter_by_location', 'filter_by_experience'], true, 3),
    createMockProvider('internshala', ['search', 'filter_by_location'], true, 8),
    createMockProvider('freshersworld', ['search', 'filter_by_location'], true, 10),
  ])
; (providerRegistry.getAll as any).mockReturnValue((providerRegistry.getEnabled as any)())
; (providerRegistry.get as any).mockImplementation((id: ProviderId) => {
    const providers = (providerRegistry.getEnabled as any)()
    return providers.find((p: any) => p.id === id) || null
  })
; (providerHealthService.get as any).mockReturnValue(defaultHealth)
; (providerHealthService.recordSuccess as any).mockReturnValue(undefined)
; (providerHealthService.recordFailure as any).mockReturnValue(undefined)
})

describe('DEFAULT_ROUTING_POLICY', () => {
  it('has correct defaults', () => {
    expect(DEFAULT_ROUTING_POLICY.enabled).toBe(true)
    expect(DEFAULT_ROUTING_POLICY.maxConcurrency).toBe(5)
    expect(DEFAULT_ROUTING_POLICY.timeout).toBe(30000)
    expect(DEFAULT_ROUTING_POLICY.enableHealthAware).toBe(true)
    expect(DEFAULT_ROUTING_POLICY.enableFallback).toBe(true)
    expect(DEFAULT_ROUTING_POLICY.enableDuplicateResolution).toBe(true)
  })
})

describe('DEFAULT_ROUTING_CONFIGURATION', () => {
  it('has correct defaults', () => {
    expect(DEFAULT_ROUTING_CONFIGURATION.concurrency).toBe(5)
    expect(DEFAULT_ROUTING_CONFIGURATION.timeout).toBe(30000)
    expect(DEFAULT_ROUTING_CONFIGURATION.preferredProviders).toEqual([])
    expect(DEFAULT_ROUTING_CONFIGURATION.excludedProviders).toEqual([])
  })
})

describe('providerMetadataService', () => {
  it('returns metadata for known providers', () => {
    const meta = providerMetadataService.get('linkedin')
    expect(meta).toBeDefined()
    expect(meta.id).toBe('linkedin')
    expect(meta.name).toBe('LinkedIn')
    expect(meta.region).toContain('global')
    expect(meta.country).toContain('us')
    expect(meta.supportsRemote).toBe(true)
  })

  it('returns metadata for indian portal providers', () => {
    const naukri = providerMetadataService.get('naukri')
    expect(naukri.region).toContain('india')
    expect(naukri.country).toContain('in')
    expect(naukri.supportsFreshers).toBe(true)

    const internshala = providerMetadataService.get('internshala')
    expect(internshala.supportsInternships).toBe(true)
    expect(internshala.jobTypes).toContain('internship')
  })

  it('returns metadata for ATS providers', () => {
    const gh = providerMetadataService.get('greenhouse')
    expect(gh.region).toContain('global')
    expect(gh.featureSupport).toContain('ats_integration')
  })

  it('returns fallback metadata for unknown providers', () => {
    const meta = providerMetadataService.get('unknown' as ProviderId)
    expect(meta.id).toBe('unknown')
    expect(meta.reliabilityScore).toBe(0.5)
    expect(meta.priority).toBe(100)
  })

  it('getAll returns all 20 providers', () => {
    const all = providerMetadataService.getAll()
    expect(all.length).toBeGreaterThanOrEqual(20)
    const ids = all.map(m => m.id)
    expect(ids).toContain('linkedin')
    expect(ids).toContain('indeed')
    expect(ids).toContain('naukri')
    expect(ids).toContain('greenhouse')
    expect(ids).toContain('successfactors')
  })

  it('getByRegion filters correctly', () => {
    const india = providerMetadataService.getByRegion('india')
    expect(india.length).toBeGreaterThanOrEqual(5)
    expect(india.map(m => m.id)).toContain('naukri')
    expect(india.map(m => m.id)).toContain('internshala')

    const global = providerMetadataService.getByRegion('global')
    expect(global.length).toBeGreaterThanOrEqual(15)
  })

  it('getByJobType filters correctly', () => {
    const internships = providerMetadataService.getByJobType('internship')
    expect(internships.map(m => m.id)).toContain('internshala')
    expect(internships.map(m => m.id)).toContain('linkedin')

    const freshers = providerMetadataService.getByJobType('fresher')
    expect(freshers.map(m => m.id)).toContain('freshersworld')
  })

  it('tracks health check timestamps', () => {
    expect(providerMetadataService.get('linkedin').lastSuccessfulHealthCheck).toBeNull()
    providerMetadataService.updateHealthCheck('linkedin', true)
    expect(providerMetadataService.get('linkedin').lastSuccessfulHealthCheck).not.toBeNull()
  })
})

describe('capabilityResolver', () => {
  it('resolveBySearchParams includes providers with matching capabilities', () => {
    const ids = capabilityResolver.resolveBySearchParams(makeSearchParams())
    expect(ids.length).toBeGreaterThan(0)
    expect(ids).toContain('linkedin')
    expect(ids).toContain('indeed')
  })

  it('resolveBySearchParams filters by location capability', () => {
    const ids = capabilityResolver.resolveBySearchParams(makeSearchParams({ location: 'Bangalore' }))
    expect(ids).toContain('linkedin')
    expect(ids).toContain('naukri')
  })

  it('resolveBySearchParams filters by easy_apply capability', () => {
    const ids = capabilityResolver.resolveBySearchParams(makeSearchParams({ easyApplyOnly: true }))
    expect(ids).toContain('linkedin')
    expect(ids).toContain('indeed')
  })

  it('resolveByJobType includes fresher-friendly providers for entry level', () => {
    const ids = capabilityResolver.resolveByJobType(makeSearchParams({ experienceLevel: 'entry' }))
    expect(ids).toContain('freshersworld')
    expect(ids).toContain('naukri')
  })

  it('resolveByJobType includes internship providers', () => {
    const ids = capabilityResolver.resolveByJobType(makeSearchParams({ employmentType: 'internship' }))
    expect(ids).toContain('internshala')
    expect(ids).toContain('linkedin')
  })

  it('resolveForRemote includes all when remote is any', () => {
    const ids = capabilityResolver.resolveForRemote(makeSearchParams({ remote: 'any' }))
    const enabled = (providerRegistry.getEnabled as any)()
    expect(ids.length).toBe(enabled.length)
  })

  it('resolveForRemote filters by supportsRemote', () => {
    const ids = capabilityResolver.resolveForRemote(makeSearchParams({ remote: 'remote' }))
    expect(ids).toContain('linkedin')
  })

  it('resolve combines all filters', () => {
    const ids = capabilityResolver.resolve(makeSearchParams({
      location: 'Mumbai',
      experienceLevel: 'entry',
    }))
    expect(ids.length).toBeGreaterThanOrEqual(1)
    expect(ids).toContain('linkedin')
    expect(ids).toContain('naukri')
  })
})

describe('healthAwareRouter', () => {
  it('isHealthy returns true for healthy provider', () => {
    expect(healthAwareRouter.isHealthy('linkedin')).toBe(true)
  })

  it('isAvailable returns true for healthy provider', () => {
    expect(healthAwareRouter.isAvailable('linkedin')).toBe(true)
  })

  it('isAvailable returns false for disabled provider', () => {
    (providerHealthService.get as any).mockReturnValueOnce({
      ...defaultHealth,
      status: 'disabled',
    })
    expect(healthAwareRouter.isAvailable('linkedin')).toBe(false)
  })

  it('evaluate includes healthy providers', () => {
    const decisions = healthAwareRouter.evaluate(['linkedin', 'indeed'])
    expect(decisions.length).toBe(2)
    expect(decisions[0].action).toBe('include')
  })

  it('evaluate skips unhealthy providers with many consecutive failures', () => {
    (providerHealthService.get as any).mockReturnValueOnce({
      ...defaultHealth,
      status: 'unhealthy',
      consecutiveFailures: 5,
    })
    const decisions = healthAwareRouter.evaluate(['linkedin'])
    expect(decisions[0].action).toBe('skip')
  })

  it('evaluate marks degraded providers as fallback', () => {
    (providerHealthService.get as any).mockReturnValueOnce({
      ...defaultHealth,
      status: 'degraded',
      consecutiveFailures: 3,
    })
    const decisions = healthAwareRouter.evaluate(['linkedin'])
    expect(decisions[0].action).toBe('fallback')
  })

  it('evaluate skips disabled providers', () => {
    (providerHealthService.get as any).mockReturnValueOnce({
      ...defaultHealth,
      status: 'disabled',
    })
    const decisions = healthAwareRouter.evaluate(['linkedin'])
    expect(decisions[0].action).toBe('skip')
  })

  it('evaluate returns reason for each decision', () => {
    const decisions = healthAwareRouter.evaluate(['linkedin'])
    expect(decisions[0].reason).toBeTruthy()
    expect(typeof decisions[0].reason).toBe('string')
  })
})

describe('rankProviders', () => {
  const baseDecisions = [
    { providerId: 'linkedin' as ProviderId, action: 'include' as const, reason: 'Healthy', priority: 1, metadata: providerMetadataService.get('linkedin'), health: defaultHealth },
    { providerId: 'internshala' as ProviderId, action: 'include' as const, reason: 'Healthy', priority: 8, metadata: providerMetadataService.get('internshala'), health: defaultHealth },
    { providerId: 'freshersworld' as ProviderId, action: 'include' as const, reason: 'Healthy', priority: 10, metadata: providerMetadataService.get('freshersworld'), health: defaultHealth },
  ]

  it('ranks higher priority providers first', () => {
    const ranked = rankProviders(baseDecisions, makeSearchParams())
    expect(ranked[0].providerId).toBe('linkedin')
    expect(ranked[ranked.length - 1].providerId).toBe('freshersworld')
  })

  it('boosts preferred providers', () => {
    const without = rankProviders(baseDecisions, makeSearchParams())
    const withPreferred = rankProviders(baseDecisions, makeSearchParams(), { preferredProviders: ['freshersworld'], excludedProviders: [], regionFilters: [], priorityOverrides: {}, concurrency: 5, timeout: 30000, fallbackPolicy: 'retry' })
    const withoutIdx = without.findIndex(d => d.providerId === 'freshersworld')
    const withIdx = withPreferred.findIndex(d => d.providerId === 'freshersworld')
    expect(withIdx).toBeLessThanOrEqual(withoutIdx)
  })

  it('removes excluded providers', () => {
    const ranked = rankProviders(baseDecisions, makeSearchParams(), { excludedProviders: ['linkedin'], preferredProviders: [], regionFilters: [], priorityOverrides: {}, concurrency: 5, timeout: 30000, fallbackPolicy: 'retry' })
    expect(ranked.find(d => d.providerId === 'linkedin')).toBeUndefined()
  })

  it('boosts providers matching search context', () => {
    const ranked = rankProviders(baseDecisions, makeSearchParams({ employmentType: 'internship' }))
    const internshalaIdx = ranked.findIndex(d => d.providerId === 'internshala')
    const freshersworldIdx = ranked.findIndex(d => d.providerId === 'freshersworld')
    expect(internshalaIdx).toBeLessThan(freshersworldIdx)
  })
})

describe('resultAggregator', () => {
  it('aggregates results from multiple providers', () => {
    const decisions = [
      { providerId: 'linkedin' as ProviderId, action: 'include' as const, reason: 'Healthy', priority: 1, metadata: providerMetadataService.get('linkedin'), health: defaultHealth },
    ]
    const result = aggregateResults(
      [{ providerId: 'linkedin', jobs: [] }],
      decisions,
      'software engineer',
    )
    expect(result.jobs).toEqual([])
    expect(result.duplicates).toEqual([])
    expect(result.normalizedCount).toBe(0)
  })

  it('handles empty sources', () => {
    const result = aggregateResults([], [], 'test')
    expect(result.jobs).toEqual([])
    expect(result.normalizedCount).toBe(0)
  })
})

describe('searchAnalyticsService', () => {
  it('creates a session with correlation id', () => {
    const analytics = searchAnalyticsService.createSession('test-123')
    expect(analytics.correlationId).toBe('test-123')
    expect(analytics.providersSearched).toBe(0)
    expect(analytics.providersSkipped).toBe(0)
    expect(analytics.providersFailed).toBe(0)
  })

  it('records provider results', () => {
    const analytics = searchAnalyticsService.createSession('test-1')
    searchAnalyticsService.recordProviderResult(analytics, 'linkedin', 100, true, 5)
    expect(analytics.providersSearched).toBe(1)
    expect(analytics.jobsFound).toBe(5)
  })

  it('records failures', () => {
    const analytics = searchAnalyticsService.createSession('test-2')
    searchAnalyticsService.recordProviderResult(analytics, 'linkedin', 100, false, 0)
    expect(analytics.providersFailed).toBe(1)
    expect(analytics.failures.length).toBe(1)
  })

  it('records skips', () => {
    const analytics = searchAnalyticsService.createSession('test-3')
    searchAnalyticsService.recordSkip(analytics, 'linkedin')
    expect(analytics.providersSkipped).toBe(1)
  })

  it('records fallbacks', () => {
    const analytics = searchAnalyticsService.createSession('test-4')
    searchAnalyticsService.recordFallback(analytics, 'linkedin')
    expect(analytics.providersFallback).toBe(1)
  })

  it('finalizes analytics correctly', () => {
    const analytics = searchAnalyticsService.createSession('test-5')
    searchAnalyticsService.recordProviderResult(analytics, 'linkedin', 200, true, 10)
    searchAnalyticsService.recordProviderResult(analytics, 'indeed', 300, true, 5)

    const finalized = searchAnalyticsService.finalize(analytics, 5000, 3, 12)
    expect(finalized.executionTime).toBe(5000)
    expect(finalized.duplicatesRemoved).toBe(3)
    expect(finalized.uniqueJobs).toBe(12)
    expect(finalized.averageLatency).toBe(250)
    expect(finalized.successRate).toBe(1)
  })

  it('persists analytics to history', () => {
    const analytics = searchAnalyticsService.createSession('test-6')
    searchAnalyticsService.finalize(analytics, 1000, 0, 5)
    const history = searchAnalyticsService.getHistory()
    expect(history.length).toBeGreaterThanOrEqual(1)
    expect(history[0].correlationId).toBe('test-6')
  })

  it('builds summary from history', () => {
    const a1 = searchAnalyticsService.createSession('s1')
    searchAnalyticsService.recordProviderResult(a1, 'linkedin', 100, true, 10)
    searchAnalyticsService.finalize(a1, 1000, 2, 8)

    const a2 = searchAnalyticsService.createSession('s2')
    searchAnalyticsService.recordProviderResult(a2, 'indeed', 200, true, 5)
    searchAnalyticsService.finalize(a2, 2000, 1, 4)

    const summary = searchAnalyticsService.getSummary()
    expect(summary.totalSearches).toBeGreaterThanOrEqual(2)
    expect(summary.totalJobsFound).toBeGreaterThanOrEqual(15)
  })
})

describe('providerRouter', () => {
  it('returns a RoutingResult with discoveryResult and analytics', async () => {
    const result = await providerRouter.search(makeSearchParams())
    expect(result).toHaveProperty('discoveryResult')
    expect(result).toHaveProperty('analytics')
    expect(result.discoveryResult.query).toBe('software engineer')
    expect(result.discoveryResult).toHaveProperty('jobs')
    expect(result.discoveryResult).toHaveProperty('errors')
    expect(result.analytics).toHaveProperty('correlationId')
  })

  it('returns valid status for successful search', async () => {
    const result = await providerRouter.search(makeSearchParams())
    expect(['completed', 'partial', 'failed']).toContain(result.discoveryResult.status)
  })

  it('filters by providers option', async () => {
    const result = await providerRouter.search(makeSearchParams(), {
      providers: ['linkedin', 'indeed'],
    })
    expect(result.discoveryResult.providersUsed).toContain('linkedin')
  })

  it('accepts custom policy', async () => {
    const result = await providerRouter.search(makeSearchParams(), {
      policy: { enableHealthAware: false, maxConcurrency: 10 },
    })
    expect(result.discoveryResult).toBeDefined()
  })

  it('accepts custom configuration', async () => {
    const result = await providerRouter.search(makeSearchParams(), {
      config: { concurrency: 3, timeout: 15000, preferredProviders: [], excludedProviders: [], regionFilters: [], priorityOverrides: {}, fallbackPolicy: 'retry' },
    })
    expect(result.discoveryResult).toBeDefined()
  })

  it('tracks analytics during search', async () => {
    const result = await providerRouter.search(makeSearchParams())
    expect(result.analytics.totalProviders).toBeGreaterThanOrEqual(0)
    expect(result.analytics.providersSearched).toBeGreaterThanOrEqual(0)
    expect(typeof result.analytics.averageLatency).toBe('number')
    expect(typeof result.analytics.successRate).toBe('number')
  })

  it('handles empty search gracefully', async () => {
    const result = await providerRouter.search(makeSearchParams({ keywords: '' }))
    expect(result.discoveryResult).toBeDefined()
  })
})
