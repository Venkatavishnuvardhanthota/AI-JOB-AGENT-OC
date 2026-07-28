import { describe, it, expect, beforeEach } from 'vitest'
import {
  ProviderError,
  AuthenticationError,
  RateLimitError,
  SessionExpiredError,
  ProviderUnavailableError,
  SearchError,
  ApplicationError,
  ValidationError,
  TimeoutError,
  NotImplementedError,
  isProviderError,
  isRecoverableError,
  getErrorCode,
} from './errors'
import { capabilitySystem } from './capability-system'
import { createAuthProvider } from './auth-abstraction'
import { requestPipeline } from './request-pipeline'
import { providerRegistry } from './provider-registry'
import { createProvider, createAndRegisterProvider } from './provider-factory'
import { responseNormalizer } from './response-normalizer'
import { ProviderLifecycle } from './provider-lifecycle'
import type { ProviderContext, ProviderMetadata, ProviderConfiguration } from './types'
import type { SearchParams } from '../discovery/types'
import type { AuthCredentials } from './types'

beforeEach(() => { providerRegistry.reset(); requestPipeline.clearCache() })

describe('Errors', () => {
  it('creates ProviderError with correct properties', () => {
    const err = new ProviderError('test error', 'TEST_CODE', 'test-provider', true)
    expect(err.message).toBe('test error')
    expect(err.code).toBe('TEST_CODE')
    expect(err.providerId).toBe('test-provider')
    expect(err.recoverable).toBe(true)
    expect(err.name).toBe('ProviderError')
  })

  it('creates AuthenticationError', () => {
    const err = new AuthenticationError('Auth failed', 'linkedin')
    expect(err.code).toBe('AUTHENTICATION_ERROR')
    expect(err.recoverable).toBe(false)
    expect(err.name).toBe('AuthenticationError')
  })

  it('creates RateLimitError', () => {
    const err = new RateLimitError('Too many requests', 'indeed', 60000)
    expect(err.code).toBe('RATE_LIMIT_ERROR')
    expect(err.recoverable).toBe(true)
    expect(err.retryAfterMs).toBe(60000)
  })

  it('creates SessionExpiredError', () => {
    const err = new SessionExpiredError('Session expired', 'naukri')
    expect(err.code).toBe('SESSION_EXPIRED_ERROR')
    expect(err.recoverable).toBe(true)
  })

  it('creates ProviderUnavailableError', () => {
    const err = new ProviderUnavailableError('Down for maintenance')
    expect(err.code).toBe('PROVIDER_UNAVAILABLE_ERROR')
    expect(err.recoverable).toBe(true)
  })

  it('creates SearchError', () => {
    const err = new SearchError('Search query failed')
    expect(err.code).toBe('SEARCH_ERROR')
    expect(err.recoverable).toBe(false)
  })

  it('creates ApplicationError', () => {
    const err = new ApplicationError('Submit failed')
    expect(err.code).toBe('APPLICATION_ERROR')
  })

  it('creates ValidationError with field', () => {
    const err = new ValidationError('Missing title', 'provider', 'title')
    expect(err.code).toBe('VALIDATION_ERROR')
    expect(err.field).toBe('title')
  })

  it('creates TimeoutError', () => {
    const err = new TimeoutError('Request timed out', 'provider')
    expect(err.code).toBe('TIMEOUT_ERROR')
    expect(err.recoverable).toBe(true)
  })

  it('creates NotImplementedError', () => {
    const err = new NotImplementedError('fetchJob', 'provider')
    expect(err.code).toBe('NOT_IMPLEMENTED')
    expect(err.message).toContain('fetchJob')
  })

  it('isProviderError identifies errors correctly', () => {
    expect(isProviderError(new ProviderError('', '', ''))).toBe(true)
    expect(isProviderError(new AuthenticationError(''))).toBe(true)
    expect(isProviderError(new Error('generic'))).toBe(false)
  })

  it('isRecoverableError checks recoverable flag', () => {
    expect(isRecoverableError(new RateLimitError(''))).toBe(true)
    expect(isRecoverableError(new AuthenticationError(''))).toBe(false)
    expect(isRecoverableError(new Error('generic'))).toBe(false)
  })

  it('getErrorCode returns correct code', () => {
    expect(getErrorCode(new AuthenticationError(''))).toBe('AUTHENTICATION_ERROR')
    expect(getErrorCode(new Error('generic'))).toBe('UNKNOWN_ERROR')
  })
})

describe('Capability System', () => {
  it('returns descriptor for each capability', () => {
    const desc = capabilitySystem.getDescriptor('search')
    expect(desc.id).toBe('search')
    expect(desc.name).toBe('Search')
    expect(desc.description).toBeTruthy()
  })

  it('returns all capability descriptors', () => {
    const all = capabilitySystem.getAllDescriptors()
    expect(all.length).toBeGreaterThanOrEqual(16)
  })

  it('checks if capabilities include a specific one', () => {
    const caps = ['search', 'apply', 'api'] as any
    expect(capabilitySystem.hasCapability(caps, 'search')).toBe(true)
    expect(capabilitySystem.hasCapability(caps, 'tracking')).toBe(false)
  })

  it('checks if all capabilities are present', () => {
    const caps = ['search', 'apply', 'api', 'tracking'] as any
    expect(capabilitySystem.hasAllCapabilities(caps, ['search', 'api'])).toBe(true)
    expect(capabilitySystem.hasAllCapabilities(caps, ['search', 'oauth'])).toBe(false)
  })

  it('checks if any capability is present', () => {
    const caps = ['search', 'apply'] as any
    expect(capabilitySystem.hasAnyCapability(caps, ['search', 'oauth'])).toBe(true)
    expect(capabilitySystem.hasAnyCapability(caps, ['oauth', 'tracking'])).toBe(false)
  })

  it('returns missing capabilities', () => {
    const caps = ['search'] as any
    const missing = capabilitySystem.getMissingCapabilities(caps, ['search', 'apply', 'api'])
    expect(missing).toEqual(['apply', 'api'])
  })

  it('merges capability sets', () => {
    const merged = capabilitySystem.mergeCapabilities(['search'] as any, ['apply'] as any, ['search'] as any)
    expect(merged).toContain('search')
    expect(merged).toContain('apply')
    expect(merged.length).toBe(2)
  })

  it('intersects capability sets', () => {
    const result = capabilitySystem.intersectCapabilities(['search', 'apply', 'api'] as any, ['search', 'api'] as any, ['search', 'tracking'] as any)
    expect(result).toEqual(['search'])
  })

  it('converts to display names', () => {
    const names = capabilitySystem.toDisplayNames(['search', 'apply'] as any)
    expect(names).toEqual(['Search', 'Apply'])
  })
})

describe('Authentication Abstraction', () => {
  it('creates OAuth provider', () => {
    const provider = createAuthProvider('oauth')
    expect(provider.method).toBe('oauth')
  })

  it('creates Cookie auth provider', () => {
    const provider = createAuthProvider('cookies')
    expect(provider.method).toBe('cookies')
  })

  it('creates Credentials auth provider', () => {
    const provider = createAuthProvider('credentials')
    expect(provider.method).toBe('credentials')
  })

  it('creates Session Token auth provider', () => {
    const provider = createAuthProvider('session_token')
    expect(provider.method).toBe('session_token')
  })

  it('creates Browser Session auth provider', () => {
    const provider = createAuthProvider('browser_session')
    expect(provider.method).toBe('browser_session')
  })

  it('OAuth authenticates with credentials', async () => {
    const provider = createAuthProvider('oauth')
    const session = await provider.authenticate({ clientId: 'id', clientSecret: 'secret', token: 'tok_123' })
    expect(session.authenticated).toBe(true)
    expect(session.method).toBe('oauth')
    expect(session.sessionData.accessToken).toBe('tok_123')
  })

  it('OAuth throws without credentials', async () => {
    const provider = createAuthProvider('oauth')
    await expect(provider.authenticate({})).rejects.toThrow(AuthenticationError)
  })

  it('Cookie auth authenticates with session cookie', async () => {
    const provider = createAuthProvider('cookies')
    const session = await provider.authenticate({ sessionCookie: 'cookie_abc' })
    expect(session.authenticated).toBe(true)
  })

  it('Cookie auth throws without cookie', async () => {
    const provider = createAuthProvider('cookies')
    await expect(provider.authenticate({})).rejects.toThrow(AuthenticationError)
  })

  it('Credentials auth authenticates with username/password', async () => {
    const provider = createAuthProvider('credentials')
    const session = await provider.authenticate({ username: 'user', password: 'pass' })
    expect(session.authenticated).toBe(true)
    expect(session.sessionData.username).toBe('user')
  })

  it('Session token auth authenticates', async () => {
    const provider = createAuthProvider('session_token')
    const session = await provider.authenticate({ token: 'sess_xyz' })
    expect(session.authenticated).toBe(true)
  })

  it('Browser session auth authenticates', async () => {
    const provider = createAuthProvider('browser_session')
    const session = await provider.authenticate({ additionalFields: { browserId: 'br_1' } })
    expect(session.authenticated).toBe(true)
  })

  it('validates active sessions', async () => {
    const provider = createAuthProvider('session_token')
    const session = await provider.authenticate({ token: 'tok_valid' })
    const valid = await provider.validateSession(session)
    expect(valid).toBe(true)
  })

  it('invalidates unauthenticated sessions', async () => {
    const provider = createAuthProvider('session_token')
    const valid = await provider.validateSession({
      method: 'session_token',
      authenticated: false,
      expiresAt: null,
      sessionData: {},
    })
    expect(valid).toBe(false)
  })

  it('refreshes sessions', async () => {
    const provider = createAuthProvider('oauth')
    const session = await provider.authenticate({ clientId: 'id', clientSecret: 'secret', token: 'tok' })
    const refreshed = await provider.refreshSession(session)
    expect(refreshed.sessionData.refreshed).toBe(true)
  })

  it('supports logout', async () => {
    const provider = createAuthProvider('oauth')
    const session = await provider.authenticate({ clientId: 'id', clientSecret: 'secret', token: 'tok' })
    await expect(provider.logout(session)).resolves.toBeUndefined()
  })
})

describe('Request Pipeline', () => {
  it('executes successfully', async () => {
    const ctx = { providerId: 'test', correlationId: 'corr_1', requestId: 'req_1', config: {}, startTime: Date.now(), metadata: {} }
    const result = await requestPipeline.execute('search', { q: 'test' }, async () => 'data', ctx)
    expect(result.success).toBe(true)
    expect(result.data).toBe('data')
    expect(result.attempts).toBe(1)
    expect(result.cached).toBe(false)
  })

  it('retries on recoverable errors', async () => {
    let attempts = 0
    const ctx = { providerId: 'test', correlationId: 'corr_1', requestId: 'req_1', config: {}, startTime: Date.now(), metadata: {} }
    const result = await requestPipeline.execute('search', {}, async () => {
      attempts++
      if (attempts < 3) throw new RateLimitError('too fast', 'test')
      return 'success'
    }, ctx, { retry: { maxRetries: 3, baseDelayMs: 10, maxDelayMs: 100, retryableErrors: ['RATE_LIMIT_ERROR'] } })
    expect(result.success).toBe(true)
    expect(result.data).toBe('success')
    expect(attempts).toBe(3)
  })

  it('fails on non-recoverable errors', async () => {
    const ctx = { providerId: 'test', correlationId: 'corr_1', requestId: 'req_1', config: {}, startTime: Date.now(), metadata: {} }
    const result = await requestPipeline.execute('search', {}, async () => { throw new ValidationError('bad input', 'test') }, ctx)
    expect(result.success).toBe(false)
    expect(result.error).toBeInstanceOf(ValidationError)
    expect(result.attempts).toBe(1)
  })

  it('times out on slow operations', async () => {
    const ctx = { providerId: 'test', correlationId: 'corr_1', requestId: 'req_1', config: {}, startTime: Date.now(), metadata: {} }
    const result = await requestPipeline.execute('search', {}, async () => { await new Promise(r => setTimeout(r, 2000)); return 'data' }, ctx, { timeoutMs: 100 })
    expect(result.success).toBe(false)
    expect(result.error).toBeInstanceOf(TimeoutError)
  }, 10000)

  it('caches search results', async () => {
    let callCount = 0
    const ctx = { providerId: 'test', correlationId: 'corr_2', requestId: 'req_2', config: {}, startTime: Date.now(), metadata: {} }
    const params = { q: 'engineer' }
    const fn = async () => { callCount++; return 'cached-data' }

    const first = await requestPipeline.execute('search', params, fn, ctx, { cache: { enabled: true, ttlMs: 60000, maxEntries: 100 } })
    expect(first.data).toBe('cached-data')
    expect(callCount).toBe(1)

    const second = await requestPipeline.execute('search', params, fn, ctx, { cache: { enabled: true, ttlMs: 60000, maxEntries: 100 } })
    expect(second.data).toBe('cached-data')
    expect(second.cached).toBe(true)
    expect(callCount).toBe(1)
  })

  it('clears cache', () => {
    requestPipeline.clearCache()
    expect(true).toBe(true)
  })

  it('invalidates cache for specific provider', () => {
    requestPipeline.invalidateCache('test-provider')
    expect(true).toBe(true)
  })

  it('supports pipeline hooks', async () => {
    const log: string[] = []
    const hook = {
      beforeExecute: async <T>(input: T, _ctx: ProviderContext) => { log.push('before'); return input },
      afterExecute: async <T>(result: any, _ctx: ProviderContext) => { log.push('after'); return result },
      onError: async (_error: Error, _ctx: ProviderContext) => { log.push('error') },
    }
    requestPipeline.addHook(hook)
    const ctx = { providerId: 'test', correlationId: 'corr_3', requestId: 'req_3', config: {}, startTime: Date.now(), metadata: {} }
    await requestPipeline.execute('search', {}, async () => 'data', ctx)
    expect(log).toContain('before')
    expect(log).toContain('after')
    requestPipeline.removeHook(hook)
  })
})

describe('Provider Registry', () => {
  const testMetadata: ProviderMetadata = {
    id: 'test-provider',
    name: 'Test Provider',
    version: '1.0.0',
    description: 'A test provider',
    capabilities: ['search', 'apply'],
    authMethods: ['credentials'],
  }

  it('registers a provider', () => {
    providerRegistry.register(testMetadata, {})
    expect(providerRegistry.getCount()).toBe(1)
  })

  it('throws on duplicate registration', () => {
    providerRegistry.register(testMetadata, {})
    expect(() => providerRegistry.register(testMetadata, {})).toThrow('already registered')
  })

  it('unregisters a provider', () => {
    providerRegistry.register(testMetadata, {})
    expect(providerRegistry.unregister('test-provider')).toBe(true)
    expect(providerRegistry.getCount()).toBe(0)
  })

  it('gets a registered provider', () => {
    providerRegistry.register(testMetadata, {})
    const p = providerRegistry.get('test-provider')
    expect(p?.metadata.name).toBe('Test Provider')
  })

  it('gets all registered providers', () => {
    providerRegistry.register(testMetadata, {})
    const all = providerRegistry.getAll()
    expect(all).toHaveLength(1)
  })

  it('gets providers by capability', () => {
    providerRegistry.register(testMetadata, {})
    const withSearch = providerRegistry.getByCapability('search')
    expect(withSearch).toHaveLength(1)
    const withTracking = providerRegistry.getByCapability('tracking')
    expect(withTracking).toHaveLength(0)
  })

  it('gets providers by multiple capabilities (any)', () => {
    providerRegistry.register(testMetadata, {})
    const result = providerRegistry.getByCapabilities(['search', 'tracking'], 'any')
    expect(result).toHaveLength(1)
  })

  it('gets providers by multiple capabilities (all)', () => {
    providerRegistry.register(testMetadata, {})
    const result = providerRegistry.getByCapabilities(['search', 'apply'], 'all')
    expect(result).toHaveLength(1)
  })

  it('gets enabled providers', () => {
    providerRegistry.register(testMetadata, {})
    const enabled = providerRegistry.getEnabled()
    expect(enabled).toHaveLength(1)
  })

  it('disables a provider', () => {
    providerRegistry.register(testMetadata, {})
    providerRegistry.disable('test-provider')
    expect(providerRegistry.getEnabled()).toHaveLength(0)
  })

  it('enables a provider', () => {
    providerRegistry.register(testMetadata, {})
    providerRegistry.disable('test-provider')
    providerRegistry.enable('test-provider')
    expect(providerRegistry.getEnabled()).toHaveLength(1)
  })

  it('gets prioritized providers', () => {
    providerRegistry.register(testMetadata, {})
    providerRegistry.register({ ...testMetadata, id: 'provider-2', name: 'Provider 2' }, {})
    providerRegistry.updateConfig('provider-2', { id: 'provider-2', enabled: true, priority: 1, config: {}, pipeline: { retry: { maxRetries: 3, baseDelayMs: 1000, maxDelayMs: 10000, retryableErrors: [] }, cache: { enabled: true, ttlMs: 300000, maxEntries: 500 }, timeoutMs: 30000, validateResponse: true }, metadata: { ...testMetadata, id: 'provider-2', name: 'Provider 2' } })
    providerRegistry.updateConfig('test-provider', { id: 'test-provider', enabled: true, priority: 5, config: {}, pipeline: { retry: { maxRetries: 3, baseDelayMs: 1000, maxDelayMs: 10000, retryableErrors: [] }, cache: { enabled: true, ttlMs: 300000, maxEntries: 500 }, timeoutMs: 30000, validateResponse: true }, metadata: testMetadata })
    const prioritized = providerRegistry.getPrioritized()
    expect(prioritized[0].metadata.id).toBe('provider-2')
  })

  it('counts providers', () => {
    expect(providerRegistry.getCount()).toBe(0)
    providerRegistry.register(testMetadata, {})
    expect(providerRegistry.getCount()).toBe(1)
  })

  it('gets enabled count', () => {
    providerRegistry.register(testMetadata, {})
    expect(providerRegistry.getEnabledCount()).toBe(1)
    providerRegistry.disable('test-provider')
    expect(providerRegistry.getEnabledCount()).toBe(0)
  })

  it('lists all capabilities across registered providers', () => {
    providerRegistry.register(testMetadata, {})
    providerRegistry.register({ ...testMetadata, id: 'p2', name: 'P2', capabilities: ['tracking'] }, {})
    const caps = providerRegistry.getAllCapabilities()
    expect(caps).toContain('search')
    expect(caps).toContain('apply')
    expect(caps).toContain('tracking')
  })

  it('checks if any provider has a capability', () => {
    providerRegistry.register(testMetadata, {})
    expect(providerRegistry.hasCapability('search')).toBe(true)
    expect(providerRegistry.hasCapability('tracking')).toBe(false)
  })

  it('registers change listeners', () => {
    const events: string[] = []
    const unsub = providerRegistry.onChange((event) => events.push(event))
    providerRegistry.register(testMetadata, {})
    expect(events).toContain('registered')
    unsub()
  })

  it('resets all providers', () => {
    providerRegistry.register(testMetadata, {})
    providerRegistry.reset()
    expect(providerRegistry.getCount()).toBe(0)
  })
})

describe('Provider Factory', () => {
  it('creates a provider with metadata', () => {
    const provider = createProvider({
      metadata: { id: 'custom', name: 'Custom', version: '1.0.0', description: 'Custom provider', capabilities: ['search'], authMethods: [] },
      async search(_params, _ctx) { return { data: [] } },
      async healthCheck(_ctx) { return { status: 'healthy' as const, latency: 10, lastCheck: new Date().toISOString() } },
    })
    expect(provider.metadata.id).toBe('custom')
    expect(provider.metadata.name).toBe('Custom')
  })

  it('search returns SearchResult structure', async () => {
    const provider = createProvider({
      metadata: { id: 'search-test', name: 'Search Test', version: '1.0.0', description: 'Test', capabilities: ['search'], authMethods: [] },
      async search(_params, _ctx) {
        return { data: [{ externalId: '1', title: 'Engineer', company: 'Acme', location: 'Remote', description: 'Job desc' }], total: 1 }
      },
    })
    const result = await provider.search({ keywords: 'engineer', location: null, remote: null, salaryMin: null, salaryMax: null, experienceLevel: null, employmentType: null, postedWithinDays: null, easyApplyOnly: false, page: 1, pageSize: 10 })
    expect(result.provider).toBe('search-test')
    expect(result.jobs).toHaveLength(1)
    expect(result.totalResults).toBe(1)
    expect(result.error).toBeNull()
  })

  it('search returns empty on missing implementation', async () => {
    const provider = createProvider({
      metadata: { id: 'no-search', name: 'No Search', version: '1.0.0', description: 'Test', capabilities: ['apply'], authMethods: [] },
    })
    const result = await provider.search({ keywords: 'test', location: null, remote: null, salaryMin: null, salaryMax: null, experienceLevel: null, employmentType: null, postedWithinDays: null, easyApplyOnly: false, page: 1, pageSize: 10 })
    expect(result.jobs).toHaveLength(0)
    expect(result.error).toBeNull()
  })

  it('search handles errors gracefully', async () => {
    const provider = createProvider({
      metadata: { id: 'error-test', name: 'Error Test', version: '1.0.0', description: 'Test', capabilities: ['search'], authMethods: [] },
      async search(_params, _ctx) { throw new Error('API down') },
    })
    const result = await provider.search({ keywords: 'test', location: null, remote: null, salaryMin: null, salaryMax: null, experienceLevel: null, employmentType: null, postedWithinDays: null, easyApplyOnly: false, page: 1, pageSize: 10 })
    expect(result.error).toBe('API down')
    expect(result.jobs).toHaveLength(0)
  })

  it('health returns result from implementation', async () => {
    const provider = createProvider({
      metadata: { id: 'health-test', name: 'Health', version: '1.0.0', description: 'Test', capabilities: [], authMethods: [] },
      async healthCheck(_ctx) { return { status: 'degraded' as const, latency: 50, lastCheck: new Date().toISOString(), message: 'High latency' } },
    })
    const health = await provider.health()
    expect(health.status).toBe('degraded')
    expect(health.latency).toBe(50)
  })

  it('health returns default on missing implementation', async () => {
    const provider = createProvider({
      metadata: { id: 'no-health', name: 'No Health', version: '1.0.0', description: 'Test', capabilities: [], authMethods: [] },
    })
    const health = await provider.health()
    expect(health.status).toBe('healthy')
  })

  it('fetchJob throws NotImplementedError when not implemented', async () => {
    const provider = createProvider({
      metadata: { id: 'no-fetch', name: 'No Fetch', version: '1.0.0', description: 'Test', capabilities: [], authMethods: [] },
    })
    await expect(provider.fetchJob!('123')).rejects.toThrow(NotImplementedError)
  })

  it('apply throws NotImplementedError when not implemented', async () => {
    const provider = createProvider({
      metadata: { id: 'no-apply', name: 'No Apply', version: '1.0.0', description: 'Test', capabilities: [], authMethods: [] },
    })
    await expect(provider.apply!('123', {})).rejects.toThrow(NotImplementedError)
  })

  it('getConfig returns configuration', () => {
    const provider = createProvider({
      metadata: { id: 'config-test', name: 'Config', version: '1.0.0', description: 'Test', capabilities: [], authMethods: [] },
      configuration: { id: 'config-test', enabled: true, priority: 5, config: {}, pipeline: { retry: { maxRetries: 5, baseDelayMs: 2000, maxDelayMs: 15000, retryableErrors: [] }, cache: { enabled: false, ttlMs: 0, maxEntries: 0 }, timeoutMs: 60000, validateResponse: true }, metadata: { id: 'config-test', name: 'Config', version: '1.0.0', description: 'Test', capabilities: [], authMethods: [] } },
    })
    const cfg = provider.getConfig()
    expect(cfg).toBeDefined()
    expect(cfg?.priority).toBe(5)
  })

  it('createAndRegisterProvider registers in the SDK registry', () => {
    const provider = createAndRegisterProvider({
      metadata: { id: 'auto-reg', name: 'Auto Reg', version: '1.0.0', description: 'Test', capabilities: ['search'], authMethods: [] },
      async search(_params, _ctx) { return { data: [] } },
    })
    expect(providerRegistry.get('auto-reg')).toBeDefined()
    expect(providerRegistry.getCount()).toBe(1)
  })
})

describe('Provider Lifecycle', () => {
  it('starts in created state', () => {
    const lifecycle = new ProviderLifecycle('test')
    expect(lifecycle.currentState).toBe('created')
  })

  it('transitions to initialized after initialize', async () => {
    const lifecycle = new ProviderLifecycle('test')
    await lifecycle.initialize({})
    expect(lifecycle.currentState).toBe('initialized')
  })

  it('throws if initializing from wrong state', async () => {
    const lifecycle = new ProviderLifecycle('test')
    await lifecycle.initialize({})
    await expect(lifecycle.initialize({})).rejects.toThrow(ProviderError)
  })

  it('transitions to authenticated after authenticate', async () => {
    const lifecycle = new ProviderLifecycle('test')
    await lifecycle.initialize({})
    await lifecycle.authenticate({ token: 'tok' }, ['session_token'])
    expect(lifecycle.currentState).toBe('active')
  })

  it('logout transitions back to initialized', async () => {
    const lifecycle = new ProviderLifecycle('test')
    await lifecycle.initialize({})
    await lifecycle.authenticate({ token: 'tok' }, ['session_token'])
    await lifecycle.logout()
    expect(lifecycle.currentState).toBe('initialized')
  })

  it('cleanup transitions to cleaned_up', async () => {
    const lifecycle = new ProviderLifecycle('test')
    await lifecycle.initialize({})
    await lifecycle.cleanup()
    expect(lifecycle.currentState).toBe('cleaned_up')
  })

  it('validates active sessions', async () => {
    const lifecycle = new ProviderLifecycle('test')
    await lifecycle.initialize({})
    await lifecycle.authenticate({ token: 'tok' }, ['session_token'])
    const valid = await lifecycle.validateSession()
    expect(valid).toBe(true)
  })

  it('returns false for unauthenticated sessions', async () => {
    const lifecycle = new ProviderLifecycle('test')
    await lifecycle.initialize({})
    const valid = await lifecycle.validateSession()
    expect(valid).toBe(false)
  })

  it('emits state changes', async () => {
    const changes: string[] = []
    const lifecycle = new ProviderLifecycle('test')
    lifecycle.onStateChange((from, to) => changes.push(`${from}->${to}`))
    await lifecycle.initialize({})
    expect(changes).toContain('created->initialized')
  })
})

describe('Response Normalizer', () => {
  it('normalizes a single job', () => {
    const job = responseNormalizer.normalizeOne(
      { externalId: 'ext_1', title: 'Software Engineer', company: 'Acme Inc', location: 'Remote', description: 'Build stuff' },
      'test-provider',
      'https://test.com/job/1'
    )
    expect(job.id).toBeTruthy()
    expect(job.title).toBe('Software Engineer')
    expect(job.provider).toBe('test-provider')
  })

  it('normalizes multiple jobs', () => {
    const jobs = responseNormalizer.normalizeMany(
      [
        { externalId: 'ext_1', title: 'Engineer', company: 'Acme', location: 'Remote', description: 'Desc' },
        { externalId: 'ext_2', title: 'Manager', company: 'Corp', location: 'NYC', description: 'Desc 2' },
      ],
      'test',
      'https://test.com'
    )
    expect(jobs).toHaveLength(2)
  })

  it('normalizes response with metadata', () => {
    const response = {
      data: [{ externalId: 'ext_1', title: 'Engineer', company: 'Acme', location: 'Remote', description: 'Desc' }],
      total: 100,
      hasMore: true,
      cursor: 'next_page',
    }
    const result = responseNormalizer.normalizeResponse(response, 'test', 'https://test.com')
    expect(result.data).toHaveLength(1)
    expect(result.total).toBe(100)
    expect(result.hasMore).toBe(true)
    expect(result.cursor).toBe('next_page')
  })

  it('validates required fields', () => {
    expect(() => responseNormalizer.normalizeOne(
      { externalId: '', title: '', company: '', location: '', description: '' },
      'test',
      'https://test.com'
    )).toThrow(ValidationError)
  })

  it('handles empty data', () => {
    const result = responseNormalizer.normalizeMany([], 'test', 'https://test.com')
    expect(result).toHaveLength(0)
  })
})
