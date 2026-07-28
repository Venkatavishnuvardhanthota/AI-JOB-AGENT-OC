import { describe, it, expect, beforeAll } from 'vitest'
import { linkedinProvider } from './providers/linkedin'
import { indeedProvider } from './providers/indeed'
import { naukriProvider } from './providers/naukri'
import { founditProvider } from './providers/foundit'
import { wellfoundProvider } from './providers/wellfound'
import { ycombinatorProvider } from './providers/ycombinator'
import { companyCareersProvider } from './providers/company-careers'
import { internshalaProvider } from './providers/internshala'
import { unstopProvider } from './providers/unstop'
import { freshersworldProvider } from './providers/freshersworld'
import { providerRegistry as sdkRegistry } from '../provider-sdk/provider-registry'
import { providerRegistry } from './provider-registry'
import type { JobProvider, ProviderId, SearchResult, ProviderHealth, ProviderCapability } from './types'

const ALL_PROVIDERS: JobProvider[] = [
  linkedinProvider, indeedProvider, naukriProvider, founditProvider,
  wellfoundProvider, ycombinatorProvider, companyCareersProvider,
  internshalaProvider, unstopProvider, freshersworldProvider,
]

describe('Provider Migration - SDK Creation', () => {
  it('all 10 providers are exported', () => {
    expect(ALL_PROVIDERS).toHaveLength(10)
  })

  it('each provider has unique id', () => {
    const ids = ALL_PROVIDERS.map(p => p.id)
    expect(new Set(ids).size).toBe(10)
  })

  it('each provider has all required JobProvider fields', () => {
    for (const p of ALL_PROVIDERS) {
      expect(p.id).toBeTruthy()
      expect(p.name).toBeTruthy()
      expect(typeof p.enabled).toBe('boolean')
      expect(typeof p.priority).toBe('number')
      expect(Array.isArray(p.capabilities)).toBe(true)
      expect(typeof p.search).toBe('function')
      expect(typeof p.health).toBe('function')
    }
  })

  it('each provider is registered in the SDK registry', () => {
    for (const p of ALL_PROVIDERS) {
      const registered = sdkRegistry.get(p.id)
      expect(registered).toBeDefined()
      expect(registered!.metadata.id).toBe(p.id)
    }
  })

  it('SDK registry has correct count', () => {
    expect(sdkRegistry.getCount()).toBeGreaterThanOrEqual(10)
  })
})

describe('Provider Migration - Capabilities', () => {
  const VALID_DISCOVERY_CAPS: ProviderCapability[] = [
    'search', 'filter_by_location', 'filter_by_salary', 'filter_by_experience',
    'filter_by_type', 'easy_apply', 'company_profile', 'salary_range',
  ]

  it('all capabilities are valid discovery capabilities', () => {
    for (const p of ALL_PROVIDERS) {
      for (const cap of p.capabilities) {
        expect(VALID_DISCOVERY_CAPS).toContain(cap)
      }
    }
  })

  it('linkedin has most capabilities', () => {
    expect(linkedinProvider.capabilities).toHaveLength(7)
    expect(linkedinProvider.capabilities).toContain('easy_apply')
    expect(linkedinProvider.capabilities).toContain('company_profile')
    expect(linkedinProvider.capabilities).toContain('salary_range')
  })

  it('lower priority providers have fewer capabilities', () => {
    expect(naukriProvider.capabilities).toHaveLength(4)
    expect(founditProvider.capabilities).toHaveLength(3)
    expect(internshalaProvider.capabilities).toHaveLength(3)
  })
})

describe('Provider Migration - Search', () => {
  const baseParams = {
    keywords: 'software engineer',
    location: null, remote: null, salaryMin: null, salaryMax: null,
    experienceLevel: null, employmentType: null, postedWithinDays: null,
    easyApplyOnly: false, page: 1, pageSize: 10,
  }

  for (const provider of ALL_PROVIDERS) {
    it(`${provider.id} returns SearchResult from search`, async () => {
      const result: SearchResult = await provider.search(baseParams)
      expect(Array.isArray(result.jobs)).toBe(true)
      expect(typeof result.totalResults).toBe('number')
      expect(typeof result.page).toBe('number')
      expect(typeof result.pageSize).toBe('number')
      expect(typeof result.hasMore).toBe('boolean')
      expect(result.provider).toBe(provider.id)
      expect(typeof result.duration).toBe('number')
      expect(result.error).toBeNull()
    })
  }

  it('each provider returns jobs with all required fields', async () => {
    for (const p of ALL_PROVIDERS) {
      const result = await p.search(baseParams)
      for (const job of result.jobs) {
        expect(job.externalId).toBeTruthy()
        expect(job.title).toBeTruthy()
        expect(job.company).toBeTruthy()
        expect(job.location).toBeTruthy()
        expect(job.description).toBeTruthy()
        expect(job.currency).toBeTruthy()
      }
    }
  })

  it('search respects page and pageSize', async () => {
    const smallParams = { ...baseParams, pageSize: 3 }
    for (const p of ALL_PROVIDERS) {
      const result = await p.search(smallParams)
      expect(result.pageSize).toBe(3)
      expect(result.jobs.length).toBeLessThanOrEqual(3)
    }
  })

  it('linkedin prioritizes higher', () => {
    expect(linkedinProvider.priority).toBeLessThan(freshersworldProvider.priority)
  })
})

describe('Provider Migration - Health', () => {
  for (const provider of ALL_PROVIDERS) {
    it(`${provider.id} returns ProviderHealth from health`, async () => {
      const health: ProviderHealth = await provider.health()
      expect(['healthy', 'degraded', 'unhealthy']).toContain(health.status)
      expect(typeof health.successRate).toBe('number')
      expect(typeof health.averageLatency).toBe('number')
      expect(typeof health.availability).toBe('number')
      expect(typeof health.consecutiveFailures).toBe('number')
    })
  }
})

describe('Provider Migration - Registry Compatibility', () => {
  beforeAll(() => {
    localStorage.clear()
  })

  it('discovery registry returns all providers', () => {
    const all = providerRegistry.getAll()
    expect(all.length).toBeGreaterThanOrEqual(10)
  })

  it('discovery registry prioritizes correctly', () => {
    const prioritized = providerRegistry.getPrioritized()
    for (let i = 1; i < prioritized.length; i++) {
      expect(prioritized[i - 1].priority).toBeLessThanOrEqual(prioritized[i].priority)
    }
  })

  it('discovery registry returns providers grouped by capability', () => {
    const withEasyApply = providerRegistry.getByCapability('easy_apply')
    expect(withEasyApply.length).toBeGreaterThanOrEqual(1)
    expect(withEasyApply.map(p => p.id)).toContain('linkedin')
    const withCompanyProfile = providerRegistry.getByCapability('company_profile')
    expect(withCompanyProfile.map(p => p.id)).toContain('wellfound')
  })
})

describe('Provider Migration - SDK Registry Integration', () => {
  it('SDK registry can query by capability', () => {
    const withSearch = sdkRegistry.getByCapability('search')
    expect(withSearch.length).toBeGreaterThanOrEqual(10)
  })

  it('SDK registry config is accessible', () => {
    const config = sdkRegistry.getConfig('linkedin')
    expect(config).toBeDefined()
    expect(config!.enabled).toBe(true)
    expect(config!.priority).toBe(1)
  })

  it('SDK registry enables/disables work', () => {
    sdkRegistry.disable('internshala')
    expect(sdkRegistry.getConfig('internshala')!.enabled).toBe(false)
    sdkRegistry.enable('internshala')
    expect(sdkRegistry.getConfig('internshala')!.enabled).toBe(true)
  })
})

describe('Provider Migration - Backward Compatibility', () => {
  it('original discovery engine types still work', () => {
    const provider: JobProvider = linkedinProvider
    expect(provider.id).toBe('linkedin')
  })

  it('providers can be filtered by ProviderId type', () => {
    const ids: ProviderId[] = ALL_PROVIDERS.map(p => p.id as ProviderId)
    expect(ids).toContain('linkedin')
    expect(ids).toContain('freshersworld')
  })

  it('search returns error=null on success', async () => {
    const result = await wellfoundProvider.search({
      keywords: 'react', location: null, remote: null, salaryMin: null, salaryMax: null,
      experienceLevel: null, employmentType: null, postedWithinDays: null,
      easyApplyOnly: false, page: 1, pageSize: 5,
    })
    expect(result.error).toBeNull()
  })
})
