import { describe, it, expect, beforeEach } from 'vitest'
import { CredentialBundle } from './credentials'
import { credentialStorage } from './storage'
import { AuthLifecycle } from './lifecycle'
import { authenticationRegistry } from './registry'
import { authSessionManager } from './auth-session-manager'
import { authConfiguration } from './configuration'
import { authEventEmitter } from './event-emitter'
import { validationEngine } from './validation-engine'
import { authenticationManager } from './authentication-manager'
import { authBrowserIntegration } from './browser-integration'
import { OAuthStrategy, UsernamePasswordStrategy, CookiesStrategy, SessionTokenStrategy, BrowserSessionStrategy, ApiKeyStrategy, AnonymousStrategy } from './strategies'
import { AuthenticationError, SessionExpiredError } from '../provider-sdk/errors'
import type { AuthMethodType, ValidationResult } from './types'
import type { AuthenticationStrategy } from './strategies/base-strategy'

beforeEach(() => {
  localStorage.clear()
  authenticationRegistry.reset()
  authEventEmitter.removeAll()
  authConfiguration.reset()
})

describe('CredentialBundle', () => {
  it('stores and retrieves values', () => {
    const bundle = new CredentialBundle({ username: 'user', password: 'pass' })
    expect(bundle.username).toBe('user')
    expect(bundle.password).toBe('pass')
  })

  it('creates from username/password', () => {
    const bundle = CredentialBundle.fromUsernamePassword('alice', 'secret')
    expect(bundle.username).toBe('alice')
    expect(bundle.password).toBe('secret')
  })

  it('creates from token', () => {
    const bundle = CredentialBundle.fromToken('tok_123')
    expect(bundle.token).toBe('tok_123')
  })

  it('creates from API key', () => {
    const bundle = CredentialBundle.fromApiKey('ak_abc')
    expect(bundle.apiKey).toBe('ak_abc')
  })

  it('creates from OAuth', () => {
    const bundle = CredentialBundle.fromOAuth('client_id', 'client_secret')
    expect(bundle.clientId).toBe('client_id')
    expect(bundle.clientSecret).toBe('client_secret')
  })

  it('creates from cookie', () => {
    const bundle = CredentialBundle.fromCookie('sess_cookie')
    expect(bundle.sessionCookie).toBe('sess_cookie')
  })

  it('validates required fields', () => {
    const bundle = new CredentialBundle()
    const errors = bundle.validateRequired(['username', 'password'])
    expect(errors).toHaveLength(2)
    expect(errors[0].field).toBe('username')
    expect(errors[1].field).toBe('password')
  })

  it('passes validation when fields present', () => {
    const bundle = CredentialBundle.fromUsernamePassword('u', 'p')
    const errors = bundle.validateRequired(['username', 'password'])
    expect(errors).toHaveLength(0)
  })

  it('toRecord excludes sensitive fields', () => {
    const bundle = new CredentialBundle({ username: 'user', password: 'secret', token: 'tok', email: 'a@b.com' })
    const record = bundle.toRecord()
    expect(record.email).toBe('a@b.com')
    expect(record.password).toBeUndefined()
    expect(record.token).toBeUndefined()
  })

  it('seals prevent further modification', () => {
    const bundle = new CredentialBundle()
    bundle.set('key', 'value')
    bundle.seal()
    expect(bundle.isSealed).toBe(true)
    expect(() => bundle.set('key2', 'value2')).toThrow('sealed')
  })
})

describe('CredentialStorage', () => {
  beforeEach(() => { credentialStorage.clear() })

  it('stores and loads values', () => {
    credentialStorage.save('test_key', { hello: 'world' })
    const loaded = credentialStorage.load('test_key')
    expect(loaded).toEqual({ hello: 'world' })
  })

  it('returns null for missing keys', () => {
    expect(credentialStorage.load('nonexistent')).toBeNull()
  })

  it('removes values', () => {
    credentialStorage.save('temp', 'value')
    credentialStorage.remove('temp')
    expect(credentialStorage.load('temp')).toBeNull()
  })

  it('configures storage type', () => {
    credentialStorage.configure('memory')
    expect(credentialStorage.active.type).toBe('memory')
    credentialStorage.configure('encrypted')
    expect(credentialStorage.active.type).toBe('encrypted')
  })

  it('memory storage saves and loads', () => {
    credentialStorage.configure('memory')
    credentialStorage.save('mem_key', 42)
    expect(credentialStorage.load('mem_key')).toBe(42)
  })

  it('encrypted storage saves and loads', () => {
    credentialStorage.configure('encrypted')
    credentialStorage.save('enc_key', 'secret-value')
    expect(credentialStorage.load('enc_key')).toBe('secret-value')
  })
})

describe('AuthLifecycle', () => {
  it('starts in created state', () => {
    const lc = new AuthLifecycle()
    expect(lc.state).toBe('created')
  })

  it('transitions from created to authenticating', () => {
    const lc = new AuthLifecycle()
    lc.transition('authenticating')
    expect(lc.state).toBe('authenticating')
  })

  it('transitions through full auth flow', () => {
    const lc = new AuthLifecycle()
    lc.transition('authenticating')
    lc.transition('authenticated')
    expect(lc.state).toBe('authenticated')
  })

  it('transitions to expired then back to authenticating', () => {
    const lc = new AuthLifecycle()
    lc.transition('authenticating')
    lc.transition('authenticated')
    lc.transition('expired')
    expect(lc.state).toBe('expired')
    lc.transition('authenticating')
    expect(lc.state).toBe('authenticating')
  })

  it('transitions to failed then to destroyed', () => {
    const lc = new AuthLifecycle()
    lc.transition('authenticating')
    lc.transition('failed')
    lc.transition('destroyed')
    expect(lc.state).toBe('destroyed')
  })

  it('throws on invalid transitions', () => {
    const lc = new AuthLifecycle()
    expect(() => lc.transition('authenticated')).toThrow('Invalid')
  })

  it('canTransitionTo checks validity', () => {
    const lc = new AuthLifecycle()
    expect(lc.canTransitionTo('authenticating')).toBe(true)
    expect(lc.canTransitionTo('authenticated')).toBe(false)
  })

  it('getHistory returns transition log', () => {
    const lc = new AuthLifecycle()
    lc.transition('authenticating')
    lc.transition('authenticated')
    expect(lc.getHistory()).toHaveLength(2)
  })

  it('reset clears state and history', () => {
    const lc = new AuthLifecycle()
    lc.transition('authenticating')
    lc.reset()
    expect(lc.state).toBe('created')
    expect(lc.getHistory()).toHaveLength(0)
  })

  it('static isValidTransition works', () => {
    expect(AuthLifecycle.isValidTransition('created', 'authenticating')).toBe(true)
    expect(AuthLifecycle.isValidTransition('created', 'authenticated')).toBe(false)
  })

  it('static getAvailableTransitions works', () => {
    const available = AuthLifecycle.getAvailableTransitions('authenticated')
    expect(available).toContain('validating')
    expect(available).toContain('refreshing')
    expect(available).toContain('expired')
  })
})

describe('Authentication Registry', () => {
  it('registers strategies', () => {
    const custom: AuthenticationStrategy = {
      id: 'custom_strat', name: 'Custom', method: 'oauth', description: '', configSchema: {},
      async authenticate() { return { id: '', providerId: 'p1', strategyId: 'custom_strat', method: 'oauth' as AuthMethodType, authenticated: true, createdAt: '', expiresAt: null, lastUsedAt: '', sessionData: {}, metadata: {} } },
      async validate() { return true },
      async refresh(s: any) { return s },
      async destroy() {},
      validateConfig() { return { valid: true, errors: [] } as ValidationResult },
    }
    authenticationRegistry.register(custom)
    expect(authenticationRegistry.getCount()).toBeGreaterThanOrEqual(1)
  })

  it('registers all default strategies', () => {
    authenticationRegistry.reset()
    expect(authenticationRegistry.getCount()).toBe(7)
  })

  it('throws on duplicate registration', () => {
    authenticationRegistry.reset()
    expect(() => authenticationRegistry.register(new UsernamePasswordStrategy())).toThrow('already registered')
  })

  it('unregisters strategies', () => {
    authenticationRegistry.reset()
    expect(authenticationRegistry.unregister('anonymous')).toBe(true)
    expect(authenticationRegistry.getCount()).toBe(6)
  })

  it('gets strategy by ID', () => {
    authenticationRegistry.reset()
    const s = authenticationRegistry.get('oauth')
    expect(s?.id).toBe('oauth')
    expect(s?.name).toBe('OAuth')
  })

  it('gets strategies by method', () => {
    authenticationRegistry.reset()
    const strategies = authenticationRegistry.getByMethod('oauth')
    expect(strategies).toHaveLength(1)
    expect(strategies[0].id).toBe('oauth')
  })

  it('resolves strategy by method', () => {
    authenticationRegistry.reset()
    const s = authenticationRegistry.resolve('session_token')
    expect(s?.id).toBe('session_token')
  })

  it('gets default strategy', () => {
    authenticationRegistry.reset()
    const s = authenticationRegistry.getDefault()
    expect(s?.id).toBe('username_password')
  })

  it('validates strategy config', () => {
    authenticationRegistry.reset()
    const result = authenticationRegistry.validateStrategy('oauth', {})
    expect(result.valid).toBe(true)
  })

  it('returns invalid for missing strategy', () => {
    const result = authenticationRegistry.validateStrategy('nonexistent', {})
    expect(result.valid).toBe(false)
    expect(result.errors[0].code).toBe('STRATEGY_NOT_FOUND')
  })

  it('discovers all strategies', () => {
    authenticationRegistry.reset()
    const all = authenticationRegistry.discover()
    expect(all).toHaveLength(7)
  })
})

describe('Session Manager', () => {
  it('creates sessions', () => {
    const session = authSessionManager.create('p1', 'oauth', 'oauth', { token: 'abc' }, null)
    expect(session.providerId).toBe('p1')
    expect(session.authenticated).toBe(true)
    expect(session.id).toMatch(/^sess_/)
  })

  it('gets session by ID', () => {
    const session = authSessionManager.create('p1', 'oauth', 'oauth', {}, null)
    const found = authSessionManager.get('p1', session.id)
    expect(found?.id).toBe(session.id)
  })

  it('updates session', () => {
    const session = authSessionManager.create('p1', 'oauth', 'oauth', {}, null)
    authSessionManager.update('p1', session.id, { metadata: { updated: true } })
    const found = authSessionManager.get('p1', session.id)
    expect(found?.metadata.updated).toBe(true)
  })

  it('destroys session', () => {
    const session = authSessionManager.create('p1', 'oauth', 'oauth', {}, null)
    authSessionManager.destroy('p1', session.id)
    expect(authSessionManager.get('p1', session.id)).toBeNull()
  })

  it('lists sessions by provider', () => {
    authSessionManager.create('p1', 'oauth', 'oauth', {}, null)
    authSessionManager.create('p1', 'oauth', 'oauth', {}, null)
    authSessionManager.create('p2', 'oauth', 'oauth', {}, null)
    expect(authSessionManager.listByProvider('p1')).toHaveLength(2)
    expect(authSessionManager.listByProvider('p2')).toHaveLength(1)
  })

  it('lists all sessions', () => {
    authSessionManager.create('p1', 'oauth', 'oauth', {}, null)
    authSessionManager.create('p2', 'oauth', 'oauth', {}, null)
    expect(authSessionManager.listAll()).toHaveLength(2)
  })

  it('gets active sessions', () => {
    authSessionManager.create('p1', 'oauth', 'oauth', {}, new Date(Date.now() + 3600000).toISOString())
    authSessionManager.create('p2', 'oauth', 'oauth', {}, new Date(Date.now() - 3600000).toISOString())
    expect(authSessionManager.getActive()).toHaveLength(1)
  })

  it('cleans up expired sessions', () => {
    authSessionManager.create('p1', 'oauth', 'oauth', {}, new Date(Date.now() - 3600000).toISOString())
    const count = authSessionManager.cleanupExpired()
    expect(count).toBe(1)
  })

  it('checks session existence by provider', () => {
    expect(authSessionManager.exists('nonexistent')).toBe(false)
    authSessionManager.create('p1', 'oauth', 'oauth', {}, null)
    expect(authSessionManager.exists('p1')).toBe(true)
  })

  it('counts sessions', () => {
    authSessionManager.create('p1', 'oauth', 'oauth', {}, null)
    authSessionManager.create('p1', 'oauth', 'oauth', {}, null)
    expect(authSessionManager.getCount('p1')).toBe(2)
    expect(authSessionManager.getCount()).toBe(2)
  })

  it('enforces max concurrent sessions', () => {
    for (let i = 0; i < 6; i++) {
      authSessionManager.create('p1', 'oauth', 'oauth', {}, null, { maxConcurrentSessions: 5 })
    }
    expect(authSessionManager.getCount('p1')).toBeLessThanOrEqual(5)
  })
})

describe('Validation Engine', () => {
  it('validates credentials for oauth', () => {
    const bundle = CredentialBundle.fromOAuth('id', 'secret')
    const result = validationEngine.validateCredentials(bundle, 'oauth')
    expect(result.valid).toBe(true)
  })

  it('rejects missing oauth credentials', () => {
    const bundle = new CredentialBundle()
    const result = validationEngine.validateCredentials(bundle, 'oauth')
    expect(result.valid).toBe(false)
  })

  it('validates username/password', () => {
    const bundle = CredentialBundle.fromUsernamePassword('u', 'p')
    const result = validationEngine.validateCredentials(bundle, 'username_password')
    expect(result.valid).toBe(true)
  })

  it('validates API key', () => {
    const bundle = CredentialBundle.fromApiKey('key')
    const result = validationEngine.validateCredentials(bundle, 'api_key')
    expect(result.valid).toBe(true)
  })

  it('anonymous always passes', () => {
    const bundle = new CredentialBundle()
    const result = validationEngine.validateCredentials(bundle, 'anonymous')
    expect(result.valid).toBe(true)
  })

  it('validates session', () => {
    const result = validationEngine.validateSession({
      id: 's_1', providerId: 'p1', strategyId: 'oauth', method: 'oauth',
      authenticated: true, createdAt: '', expiresAt: new Date(Date.now() + 3600000).toISOString(),
      lastUsedAt: '', sessionData: {}, metadata: {},
    })
    expect(result.valid).toBe(true)
  })

  it('rejects expired session', () => {
    const result = validationEngine.validateSession({
      id: 's_1', providerId: 'p1', strategyId: 'oauth', method: 'oauth',
      authenticated: true, createdAt: '', expiresAt: new Date(Date.now() - 3600000).toISOString(),
      lastUsedAt: '', sessionData: {}, metadata: {},
    })
    expect(result.valid).toBe(false)
    expect(result.errors[0].code).toBe('SESSION_EXPIRED')
  })

  it('validates configuration', () => {
    const result = validationEngine.validateConfiguration({ sessionTimeoutMs: 3600000 })
    expect(result.valid).toBe(true)
  })

  it('rejects invalid session timeout', () => {
    const result = validationEngine.validateConfiguration({ sessionTimeoutMs: 1000 })
    expect(result.valid).toBe(false)
  })

  it('validates policy', () => {
    const result = validationEngine.validatePolicy({
      sessionTimeoutMs: 3600000, refreshEnabled: true, refreshThresholdMs: 300000,
      maxRetries: 3, retryDelayMs: 1000, storageType: 'memory',
      validateOnResume: true, maxConcurrentSessions: 5,
    })
    expect(result.valid).toBe(true)
  })

  it('validates provider config', () => {
    const result = validationEngine.validateProvider('p1', { key: 'val' })
    expect(result.valid).toBe(true)
  })

  it('rejects missing provider ID', () => {
    const result = validationEngine.validateProvider('', { key: 'val' })
    expect(result.valid).toBe(false)
  })

  it('gets required fields for each method', () => {
    expect(validationEngine.getRequiredFields('oauth')).toContain('clientId')
    expect(validationEngine.getRequiredFields('username_password')).toContain('password')
    expect(validationEngine.getRequiredFields('api_key')).toContain('apiKey')
    expect(validationEngine.getRequiredFields('anonymous')).toHaveLength(0)
  })
})

describe('Configuration', () => {
  it('returns default configuration', () => {
    const cfg = authConfiguration.get()
    expect(cfg.sessionTimeoutMs).toBe(3600000)
    expect(cfg.refreshEnabled).toBe(true)
  })

  it('updates configuration', () => {
    authConfiguration.update({ sessionTimeoutMs: 7200000 })
    expect(authConfiguration.get().sessionTimeoutMs).toBe(7200000)
  })

  it('sets storage type', () => {
    authConfiguration.setStorageType('encrypted')
    expect(authConfiguration.get().storageType).toBe('encrypted')
  })

  it('sets session timeout', () => {
    authConfiguration.setSessionTimeout(1800000)
    expect(authConfiguration.get().sessionTimeoutMs).toBe(1800000)
  })

  it('resets to defaults', () => {
    authConfiguration.update({ sessionTimeoutMs: 999999 })
    authConfiguration.reset()
    expect(authConfiguration.get().sessionTimeoutMs).toBe(3600000)
  })

  it('throws on invalid configuration', () => {
    expect(() => authConfiguration.update({ sessionTimeoutMs: 1000 })).toThrow('Invalid')
  })
})

describe('Event Emitter', () => {
  it('emits and receives events', () => {
    const events: string[] = []
    const unsub = authEventEmitter.on('authentication_succeeded', (p) => events.push(p.strategyId))
    authEventEmitter.emit('authentication_succeeded', { providerId: 'p1', strategyId: 'oauth', sessionId: 's1', timestamp: '' })
    expect(events).toContain('oauth')
    unsub()
  })

  it('removes listeners via returned function', () => {
    let count = 0
    const unsub = authEventEmitter.on('authentication_failed', () => count++)
    unsub()
    authEventEmitter.emit('authentication_failed', { providerId: 'p1', strategyId: 'oauth', error: 'err', timestamp: '' })
    expect(count).toBe(0)
  })

  it('removes listeners via off', () => {
    let count = 0
    const fn = () => count++
    authEventEmitter.on('session_refreshed', fn)
    authEventEmitter.off('session_refreshed', fn)
    authEventEmitter.emit('session_refreshed', { providerId: 'p1', sessionId: 's1', timestamp: '' })
    expect(count).toBe(0)
  })

  it('counts listeners', () => {
    authEventEmitter.on('session_expired', () => {})
    expect(authEventEmitter.listenerCount('session_expired')).toBe(1)
  })

  it('removes all listeners for an event', () => {
    authEventEmitter.on('session_destroyed', () => {})
    authEventEmitter.removeAll('session_destroyed')
    expect(authEventEmitter.listenerCount('session_destroyed')).toBe(0)
  })

  it('removes all listeners', () => {
    authEventEmitter.on('strategy_registered', () => {})
    authEventEmitter.on('strategy_unregistered', () => {})
    authEventEmitter.removeAll()
    expect(authEventEmitter.listenerCount('strategy_registered')).toBe(0)
    expect(authEventEmitter.listenerCount('strategy_unregistered')).toBe(0)
  })
})

describe('Authentication Manager - OAuth', () => {
  it('authenticates with OAuth', async () => {
    const bundle = CredentialBundle.fromOAuth('client_123', 'secret_456')
    const session = await authenticationManager.authenticate('test_provider', 'oauth', bundle)
    expect(session.authenticated).toBe(true)
    expect(session.method).toBe('oauth')
    expect(session.providerId).toBe('test_provider')
  })

  it('throws on missing OAuth credentials', async () => {
    const bundle = new CredentialBundle()
    await expect(authenticationManager.authenticate('p1', 'oauth', bundle)).rejects.toThrow(AuthenticationError)
  })
})

describe('Authentication Manager - Username/Password', () => {
  it('authenticates with username/password', async () => {
    const bundle = CredentialBundle.fromUsernamePassword('alice', 'pass')
    const session = await authenticationManager.authenticate('p1', 'username_password', bundle)
    expect(session.authenticated).toBe(true)
    expect(session.method).toBe('username_password')
  })
})

describe('Authentication Manager - Session Token', () => {
  it('authenticates with session token', async () => {
    const bundle = CredentialBundle.fromToken('tok_abc123')
    const session = await authenticationManager.authenticate('p1', 'session_token', bundle)
    expect(session.authenticated).toBe(true)
  })
})

describe('Authentication Manager - API Key', () => {
  it('authenticates with API key', async () => {
    const bundle = CredentialBundle.fromApiKey('ak_xyz')
    const session = await authenticationManager.authenticate('p1', 'api_key', bundle)
    expect(session.authenticated).toBe(true)
  })
})

describe('Authentication Manager - Anonymous', () => {
  it('authenticates anonymously', async () => {
    const bundle = new CredentialBundle()
    const session = await authenticationManager.authenticate('p1', 'anonymous', bundle)
    expect(session.authenticated).toBe(true)
    expect(session.method).toBe('anonymous')
  })
})

describe('Authentication Manager - Cookies', () => {
  it('authenticates with cookies', async () => {
    const bundle = CredentialBundle.fromCookie('sess_cookie_val')
    const session = await authenticationManager.authenticate('p1', 'cookies', bundle)
    expect(session.authenticated).toBe(true)
    expect(session.method).toBe('cookies')
  })
})

describe('Authentication Manager - Browser Session', () => {
  it('authenticates with browser session', async () => {
    const bundle = new CredentialBundle({ browserId: 'br_1', profileData: { key: 'val' } })
    const session = await authenticationManager.authenticate('p1', 'browser_session', bundle)
    expect(session.authenticated).toBe(true)
    expect(session.method).toBe('browser_session')
  })
})

describe('Authentication Manager - Session Management', () => {
  it('validates sessions', async () => {
    const bundle = CredentialBundle.fromToken('tok')
    const session = await authenticationManager.authenticate('p1', 'session_token', bundle)
    await expect(authenticationManager.validateSession('p1', session.id)).resolves.toBe(true)
  })

  it('returns false for invalid sessions', async () => {
    await expect(authenticationManager.validateSession('p1', 'nonexistent')).resolves.toBe(false)
  })

  it('refreshes sessions', async () => {
    const bundle = CredentialBundle.fromToken('tok')
    const session = await authenticationManager.authenticate('p1', 'session_token', bundle)
    const refreshed = await authenticationManager.refreshSession('p1', session.id)
    expect(refreshed.sessionData.refreshed).toBe(true)
  })

  it('throws on refresh for missing session', async () => {
    await expect(authenticationManager.refreshSession('p1', 'nonexistent')).rejects.toThrow(SessionExpiredError)
  })

  it('logs out and destroys session', async () => {
    const bundle = CredentialBundle.fromToken('tok')
    const session = await authenticationManager.authenticate('p1', 'session_token', bundle)
    authenticationManager.logout('p1', session.id)
    expect(authenticationManager.getSession('p1', session.id)).toBeNull()
  })

  it('destroys session', async () => {
    const bundle = CredentialBundle.fromToken('tok')
    const session = await authenticationManager.authenticate('p1', 'session_token', bundle)
    authenticationManager.destroySession('p1', session.id)
    expect(authenticationManager.getSession('p1', session.id)).toBeNull()
  })

  it('gets session by ID', async () => {
    const bundle = CredentialBundle.fromToken('tok')
    const session = await authenticationManager.authenticate('p1', 'session_token', bundle)
    const found = authenticationManager.getSession('p1', session.id)
    expect(found?.id).toBe(session.id)
  })
})

describe('Authentication Manager - Strategy Management', () => {
  it('registers strategies', () => {
    const custom: AuthenticationStrategy = {
      id: 'custom_mgr', name: 'Custom', method: 'username_password', description: '', configSchema: {},
      async authenticate() { return { id: '', providerId: 'p1', strategyId: 'custom_mgr', method: 'username_password' as AuthMethodType, authenticated: true, createdAt: '', expiresAt: null, lastUsedAt: '', sessionData: {}, metadata: {} } },
      async validate() { return true },
      async refresh(s: any) { return s },
      async destroy() {},
      validateConfig() { return { valid: true, errors: [] } as ValidationResult },
    }
    authenticationManager.registerStrategy(custom)
    expect(authenticationRegistry.get('custom_mgr')).toBeDefined()
  })

  it('unregisters strategies', () => {
    authenticationManager.unregisterStrategy('anonymous')
    expect(authenticationRegistry.get('anonymous')).toBeUndefined()
  })

  it('lists strategies', () => {
    const strategies = authenticationManager.getStrategies()
    const ids = strategies.map(s => s.id)
    expect(ids).toContain('oauth')
    expect(ids).toContain('username_password')
  })

  it('filters strategies by method', () => {
    const oauth = authenticationManager.getStrategies('oauth')
    expect(oauth).toHaveLength(1)
  })
})

describe('Authentication Manager - Configuration', () => {
  it('gets and updates configuration', () => {
    const cfg = authenticationManager.getConfiguration()
    expect(cfg.sessionTimeoutMs).toBe(3600000)
    authenticationManager.updateConfiguration({ sessionTimeoutMs: 7200000 })
    expect(authenticationManager.getConfiguration().sessionTimeoutMs).toBe(7200000)
  })
})

describe('Authentication Manager - Events', () => {
  it('emits authentication_succeeded event', async () => {
    const events: string[] = []
    const unsub = authenticationManager.on('authentication_succeeded', (p) => events.push(p.strategyId))
    const bundle = CredentialBundle.fromToken('tok')
    await authenticationManager.authenticate('p1', 'session_token', bundle)
    expect(events).toContain('session_token')
    unsub()
  })

  it('emits authentication_failed event', async () => {
    const events: string[] = []
    authenticationManager.on('authentication_failed', (p) => events.push(p.strategyId))
    const bundle = new CredentialBundle()
    await expect(authenticationManager.authenticate('p1', 'oauth', bundle)).rejects.toThrow()
    expect(events).toContain('oauth')
  })
})

describe('Authentication Manager - Analytics', () => {
  it('returns analytics', async () => {
    const bundle = CredentialBundle.fromToken('tok')
    await authenticationManager.authenticate('p1', 'session_token', bundle)
    const analytics = authenticationManager.getAnalytics()
    expect(analytics.totalAuthentications).toBeGreaterThanOrEqual(1)
    expect(analytics.successfulAuthentications).toBeGreaterThanOrEqual(1)
  })
})

describe('Browser Integration', () => {
  it('attaches browser session to auth session', async () => {
    const bundle = CredentialBundle.fromToken('tok')
    const session = await authenticationManager.authenticate('p1', 'session_token', bundle)
    const attachment = authenticationManager.attachBrowser(session.id, 'p1', 'br_1')
    expect(attachment.browserId).toBe('br_1')
    expect(attachment.sessionId).toBe(session.id)
  })

  it('detaches browser from auth session', async () => {
    const bundle = CredentialBundle.fromToken('tok')
    const session = await authenticationManager.authenticate('p1', 'session_token', bundle)
    authenticationManager.attachBrowser(session.id, 'p1', 'br_1')
    authenticationManager.detachBrowser(session.id, 'p1')
    const found = authenticationManager.getSession('p1', session.id)
    expect(found?.metadata.detachedAt).toBeDefined()
  })

  it('reuses browser profile', () => {
    const session = authSessionManager.create('p1', 'oauth', 'oauth', {}, null)
    const attachment = authBrowserIntegration.reuseProfile(session.id, 'p1', 'br_1')
    expect(attachment.profileReused).toBe(true)
  })

  it('imports and exports cookies', () => {
    const session = authSessionManager.create('p1', 'oauth', 'oauth', {}, null)
    const cookies = [{ name: 'session', value: 'abc' }]
    authBrowserIntegration.importCookies(session.id, 'p1', cookies)
    const exported = authBrowserIntegration.exportCookies('p1', session.id)
    expect(exported).toEqual(cookies)
  })
})

describe('Strategy Implementations', () => {
  it('OAuthStrategy validates sessions', async () => {
    const s = new OAuthStrategy()
    const session = await s.authenticate(CredentialBundle.fromOAuth('id', 'secret'), 'p1')
    expect(await s.validate(session)).toBe(true)
  })

  it('OAuthStrategy refreshes sessions', async () => {
    const s = new OAuthStrategy()
    const bundle = CredentialBundle.fromOAuth('id', 'secret', 'refresh_tok')
    const session = await s.authenticate(bundle, 'p1')
    const refreshed = await s.refresh(session)
    expect(refreshed.sessionData.refreshed).toBe(true)
  })

  it('UsernamePasswordStrategy validates sessions', async () => {
    const s = new UsernamePasswordStrategy()
    const session = await s.authenticate(CredentialBundle.fromUsernamePassword('u', 'p'), 'p1')
    expect(await s.validate(session)).toBe(true)
  })

  it('CookiesStrategy validates sessions', async () => {
    const s = new CookiesStrategy()
    const session = await s.authenticate(CredentialBundle.fromCookie('cookie'), 'p1')
    expect(await s.validate(session)).toBe(true)
  })

  it('SessionTokenStrategy validates sessions', async () => {
    const s = new SessionTokenStrategy()
    const session = await s.authenticate(CredentialBundle.fromToken('tok'), 'p1')
    expect(await s.validate(session)).toBe(true)
  })

  it('BrowserSessionStrategy validates sessions', async () => {
    const s = new BrowserSessionStrategy()
    const session = await s.authenticate(new CredentialBundle({ browserId: 'br_1' }), 'p1')
    expect(await s.validate(session)).toBe(true)
  })

  it('ApiKeyStrategy validates sessions', async () => {
    const s = new ApiKeyStrategy()
    const session = await s.authenticate(CredentialBundle.fromApiKey('ak'), 'p1')
    expect(await s.validate(session)).toBe(true)
  })

  it('AnonymousStrategy always validates', async () => {
    const s = new AnonymousStrategy()
    const session = await s.authenticate(new CredentialBundle(), 'p1')
    expect(await s.validate(session)).toBe(true)
  })

  it('OAuthStrategy destroys without error', async () => {
    const s = new OAuthStrategy()
    const session = await s.authenticate(CredentialBundle.fromOAuth('id', 'secret'), 'p1')
    await expect(s.destroy(session)).resolves.toBeUndefined()
  })

  it('strategies report method correctly', () => {
    expect(new OAuthStrategy().method).toBe('oauth')
    expect(new UsernamePasswordStrategy().method).toBe('username_password')
    expect(new CookiesStrategy().method).toBe('cookies')
    expect(new SessionTokenStrategy().method).toBe('session_token')
    expect(new BrowserSessionStrategy().method).toBe('browser_session')
    expect(new ApiKeyStrategy().method).toBe('api_key')
    expect(new AnonymousStrategy().method).toBe('anonymous')
  })

  it('strategies validate config', () => {
    expect(new OAuthStrategy().validateConfig({}).valid).toBe(true)
    expect(new UsernamePasswordStrategy().validateConfig({}).valid).toBe(true)
  })
})
