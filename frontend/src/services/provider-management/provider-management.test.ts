import { describe, it, expect, beforeEach } from 'vitest'
import { providerManagementService } from './provider-management-service'
import { getCategories, getAllCategoryNames, categorizeProvider } from './provider-categories'
import { providerMetadataService } from '../routing/provider-metadata'

describe('provider-categories', () => {
  it('categorizes ATS providers correctly', () => {
    const metadata = providerMetadataService.get('lever')
    const cat = categorizeProvider(metadata)
    expect(cat).toBe('ATS Providers')
  })

  it('categorizes startup platforms correctly', () => {
    const metadata = providerMetadataService.get('wellfound')
    const cat = categorizeProvider(metadata)
    expect(cat).toBe('Startup Platforms')
  })

  it('categorizes Indian job portals correctly', () => {
    const metadata = providerMetadataService.get('naukri')
    const cat = categorizeProvider(metadata)
    expect(cat).toBe('Indian Job Portals')
  })

  it('returns all categories with provider counts', () => {
    const providers = providerManagementService.getProviders()
    const categories = getCategories(providers)
    expect(categories.length).toBeGreaterThanOrEqual(5)
    categories.forEach(cat => {
      expect(cat.name).toBeDefined()
      expect(typeof cat.count).toBe('number')
    })
  })

  it('returns all category names', () => {
    const providers = providerManagementService.getProviders()
    const names = getAllCategoryNames(providers)
    expect(names).toContain('ATS Providers')
    expect(names).toContain('Indian Job Portals')
    expect(names).toContain('Global Job Boards')
  })
})

describe('providerManagementService', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('returns providers from the registry', () => {
    const providers = providerManagementService.getProviders()
    expect(providers.length).toBeGreaterThanOrEqual(10)
    const linkedin = providers.find(p => p.id === 'linkedin')
    expect(linkedin).toBeDefined()
    expect(linkedin!.name).toBe('LinkedIn')
  })

  it('enriches providers with categories', () => {
    const providers = providerManagementService.getProviders()
    const wellfound = providers.find(p => p.id === 'wellfound')
    expect(wellfound).toBeDefined()
    expect(wellfound!.category).toBe('Startup Platforms')
  })

  it('filters providers by search', () => {
    const results = providerManagementService.getFilteredProviders({
      search: 'linkedin',
      categories: [],
      regions: [],
      countries: [],
      healthStatuses: [],
      capabilities: [],
      enabled: null,
      sortBy: 'name',
      sortOrder: 'asc',
    })
    expect(results.length).toBeGreaterThanOrEqual(1)
    expect(results.every(p => p.name.toLowerCase().includes('linkedin'))).toBe(true)
  })

  it('filters providers by category', () => {
    const results = providerManagementService.getFilteredProviders({
      search: '',
      categories: ['Indian Job Portals'],
      regions: [],
      countries: [],
      healthStatuses: [],
      capabilities: [],
      enabled: null,
      sortBy: 'name',
      sortOrder: 'asc',
    })
    expect(results.length).toBeGreaterThan(0)
    expect(results.every(p => p.category === 'Indian Job Portals')).toBe(true)
  })

  it('filters providers by enabled status', () => {
    const results = providerManagementService.getFilteredProviders({
      search: '',
      categories: [],
      regions: [],
      countries: [],
      healthStatuses: [],
      capabilities: [],
      enabled: true,
      sortBy: 'name',
      sortOrder: 'asc',
    })
    expect(results.length).toBeGreaterThan(0)
    expect(results.every(p => p.enabled)).toBe(true)
  })

  it('sorts providers by name ascending', () => {
    const results = providerManagementService.getFilteredProviders({
      search: '',
      categories: [],
      regions: [],
      countries: [],
      healthStatuses: [],
      capabilities: [],
      enabled: null,
      sortBy: 'name',
      sortOrder: 'asc',
    })
    for (let i = 1; i < results.length; i++) {
      expect(results[i - 1].name.localeCompare(results[i].name)).toBeLessThanOrEqual(0)
    }
  })

  it('sorts providers by priority ascending', () => {
    const results = providerManagementService.getFilteredProviders({
      search: '',
      categories: [],
      regions: [],
      countries: [],
      healthStatuses: [],
      capabilities: [],
      enabled: null,
      sortBy: 'priority',
      sortOrder: 'asc',
    })
    for (let i = 1; i < results.length; i++) {
      expect(results[i - 1].priority).toBeLessThanOrEqual(results[i].priority)
    }
  })

  it('disables a provider', () => {
    providerManagementService.disableProvider('naukri')
    const providers = providerManagementService.getProviders()
    const naukri = providers.find(p => p.id === 'naukri')
    expect(naukri!.enabled).toBe(false)
  })

  it('enables a provider', () => {
    providerManagementService.disableProvider('naukri')
    providerManagementService.enableProvider('naukri')
    const providers = providerManagementService.getProviders()
    const naukri = providers.find(p => p.id === 'naukri')
    expect(naukri!.enabled).toBe(true)
  })

  it('runs health check', async () => {
    const result = await providerManagementService.runHealthCheck('linkedin')
    expect(result.status).toBeDefined()
  })

  it('returns categories with correct provider counts', () => {
    const providers = providerManagementService.getProviders()
    const categories = providerManagementService.getCategories(providers)
    const totalFromCategories = categories.reduce((sum, cat) => sum + cat.count, 0)
    const totalProviders = providerManagementService.getProviders().length
    expect(totalFromCategories).toBe(totalProviders)
  })

  it('performs bulk enable action', () => {
    providerManagementService.disableProvider('naukri')
    providerManagementService.disableProvider('indeed')
    providerManagementService.bulkAction('enable', ['naukri', 'indeed'])
    const providers = providerManagementService.getProviders()
    expect(providers.find(p => p.id === 'naukri')!.enabled).toBe(true)
    expect(providers.find(p => p.id === 'indeed')!.enabled).toBe(true)
  })

  it('performs bulk disable action', () => {
    providerManagementService.bulkAction('disable', ['linkedin', 'indeed'])
    const providers = providerManagementService.getProviders()
    expect(providers.find(p => p.id === 'linkedin')!.enabled).toBe(false)
    expect(providers.find(p => p.id === 'indeed')!.enabled).toBe(false)
  })

  it('provides default configuration', () => {
    const config = providerManagementService.getConfiguration()
    expect(config.maxProviders).toBe(20)
    expect(config.concurrentProviders).toBe(5)
    expect(config.searchTimeout).toBe(30000)
    expect(config.retryCount).toBe(2)
    expect(config.onlyHealthyProviders).toBe(false)
    expect(config.requireAuthentication).toBe(false)
  })

  it('saves and retrieves configuration', () => {
    providerManagementService.saveConfiguration({
      maxProviders: 10,
      concurrentProviders: 3,
      searchTimeout: 15000,
      retryCount: 1,
      preferredProviders: [],
      excludedProviders: [],
      fallbackProviders: [],
      regionalPriority: [],
      onlyHealthyProviders: true,
      requireAuthentication: true,
    })
    const config = providerManagementService.getConfiguration()
    expect(config.maxProviders).toBe(10)
    expect(config.concurrentProviders).toBe(3)
    expect(config.searchTimeout).toBe(15000)
    expect(config.retryCount).toBe(1)
    expect(config.onlyHealthyProviders).toBe(true)
    expect(config.requireAuthentication).toBe(true)
  })

  it('gets provider details', () => {
    const details = providerManagementService.getProviderDetails('linkedin')
    expect(details.provider).toBeDefined()
    expect(details.provider.id).toBe('linkedin')
    expect(details.metrics).toBeDefined()
    expect(details.recentSearches).toBeDefined()
    expect(details.logs).toBeDefined()
    expect(details.metrics.averageLatency).toBeGreaterThanOrEqual(0)
  })

  it('resets provider health', () => {
    providerManagementService.resetProvider('naukri')
    const providers = providerManagementService.getProviders()
    const naukri = providers.find(p => p.id === 'naukri')
    expect(naukri!.health.consecutiveFailures).toBe(0)
    expect(naukri!.health.errorCount).toBe(0)
    expect(naukri!.health.lastError).toBeNull()
  })
})
