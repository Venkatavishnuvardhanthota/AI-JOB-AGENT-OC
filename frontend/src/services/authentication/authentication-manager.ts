import type { AuthMethodType, AuthSessionRecord, AuthConfiguration, AuthEventPayload, StrategyDescriptor, AuthAnalytics, BrowserAttachment } from './types'
import type { AuthenticationStrategy } from './strategies/base-strategy'
import { CredentialBundle } from './credentials'
import { AuthLifecycle } from './lifecycle'
import { authSessionManager } from './auth-session-manager'
import { authenticationRegistry } from './registry'
import { authConfiguration } from './configuration'
import { authEventEmitter } from './event-emitter'
import { validationEngine } from './validation-engine'
import { credentialStorage } from './storage'
import { emitAuthLog, recordAuthMetric, recordAuthDuration, getAuthAnalytics } from './observability-integration'
import { authBrowserIntegration } from './browser-integration'
import { AuthenticationError, SessionExpiredError } from '../provider-sdk/errors'

export const authenticationManager = {
  async authenticate(providerId: string, method: AuthMethodType, credentials: CredentialBundle, config?: Partial<AuthConfiguration>): Promise<AuthSessionRecord> {
    const startTime = Date.now()
    const lifecycle = new AuthLifecycle()

    let strategy: AuthenticationStrategy | undefined

    try {
      lifecycle.transition('authenticating')

      strategy = authenticationRegistry.resolve(method)
      if (!strategy) {
        throw new AuthenticationError(`No strategy registered for method: ${method}`, providerId)
      }

      credentialStorage.save(`auth_creds_${providerId}`, credentials.toSecureRecord())
      const credValidation = validationEngine.validateCredentials(credentials, method)
      if (!credValidation.valid) {
        const msg = `Credential validation failed: ${credValidation.errors.map(e => e.message).join(', ')}`
        emitAuthLog(providerId, 'error', msg, { method, errors: credValidation.errors })
        throw new AuthenticationError(msg, providerId)
      }

      const authConfig = { ...authConfiguration.get(), ...config }
      const session = await strategy.authenticate(credentials, providerId)

      const record = authSessionManager.create(
        providerId, strategy.id, method,
        session.sessionData,
        session.expiresAt,
        authConfig
      )

      lifecycle.transition('authenticated')
      const duration = Date.now() - startTime
      recordAuthMetric('authentication.success', 1, { provider: providerId, strategy: strategy.id })
      recordAuthDuration('authentication.duration', duration, { provider: providerId, strategy: strategy.id })
      emitAuthLog(providerId, 'info', `Authentication succeeded via ${strategy.name}`, { strategyId: strategy.id, sessionId: record.id, durationMs: duration })
      authEventEmitter.emit('authentication_succeeded', { providerId, strategyId: strategy.id, sessionId: record.id, timestamp: new Date().toISOString() })

      return record
    } catch (error) {
      try { lifecycle.transition('failed') } catch {}
      const errMsg = error instanceof Error ? error.message : 'Unknown error'
      const duration = Date.now() - startTime
      const sid = strategy?.id ?? 'unknown'
      recordAuthMetric('authentication.failure', 1, { provider: providerId, strategy: sid, error: errMsg })
      emitAuthLog(providerId, 'error', `Authentication failed: ${errMsg}`, { method, strategyId: sid, durationMs: duration })
      authEventEmitter.emit('authentication_failed', { providerId, strategyId: sid, error: errMsg, timestamp: new Date().toISOString() })
      throw error
    }
  },

  async validateSession(providerId: string, sessionId: string): Promise<boolean> {
    const session = authSessionManager.get(providerId, sessionId)
    if (!session) return false

    const strategy = authenticationRegistry.get(session.strategyId)
    if (!strategy) return false

    if (session.expiresAt && new Date(session.expiresAt).getTime() <= Date.now()) {
      authEventEmitter.emit('session_expired', { providerId, sessionId, timestamp: new Date().toISOString() })
      return false
    }

    const valid = await strategy.validate(session)
    if (valid) {
      authSessionManager.touch(providerId, sessionId)
    }
    return valid
  },

  async refreshSession(providerId: string, sessionId: string): Promise<AuthSessionRecord> {
    const session = authSessionManager.get(providerId, sessionId)
    if (!session) throw new SessionExpiredError('Session not found', providerId)

    const strategy = authenticationRegistry.get(session.strategyId)
    if (!strategy) throw new AuthenticationError(`Strategy ${session.strategyId} not found`, providerId)

    try {
      const refreshed = await strategy.refresh(session)
      authSessionManager.update(providerId, sessionId, {
        expiresAt: refreshed.expiresAt,
        sessionData: refreshed.sessionData,
      })
      authEventEmitter.emit('session_refreshed', { providerId, sessionId, timestamp: new Date().toISOString() })
      return authSessionManager.get(providerId, sessionId)!
    } catch (error) {
      throw error
    }
  },

  logout(providerId: string, sessionId: string): void {
    const session = authSessionManager.get(providerId, sessionId)
    if (!session) return

    const strategy = authenticationRegistry.get(session.strategyId)
    if (strategy) strategy.destroy(session).catch(() => {})

    authSessionManager.destroy(providerId, sessionId)
    credentialStorage.remove(`auth_creds_${providerId}`)
    authEventEmitter.emit('session_destroyed', { providerId, sessionId, timestamp: new Date().toISOString() })
    emitAuthLog(providerId, 'info', 'Logged out and session destroyed', { sessionId })
  },

  getSession(providerId: string, sessionId: string): AuthSessionRecord | null {
    return authSessionManager.get(providerId, sessionId)
  },

  destroySession(providerId: string, sessionId: string): void {
    const session = authSessionManager.get(providerId, sessionId)
    if (!session) return

    const strategy = authenticationRegistry.get(session.strategyId)
    if (strategy) strategy.destroy(session).catch(() => {})

    authSessionManager.destroy(providerId, sessionId)
    authEventEmitter.emit('session_destroyed', { providerId, sessionId, timestamp: new Date().toISOString() })
  },

  registerStrategy(strategy: AuthenticationStrategy): void {
    authenticationRegistry.register(strategy)
    authEventEmitter.emit('strategy_registered', {
      strategyId: strategy.id,
      method: strategy.method,
      timestamp: new Date().toISOString(),
    })
  },

  unregisterStrategy(strategyId: string): void {
    authenticationRegistry.unregister(strategyId)
    authEventEmitter.emit('strategy_unregistered', { strategyId, timestamp: new Date().toISOString() })
  },

  getStrategies(method?: AuthMethodType): StrategyDescriptor[] {
    const strategies = method ? authenticationRegistry.getByMethod(method) : authenticationRegistry.getAll()
    return strategies.map(s => ({
      id: s.id,
      name: s.name,
      method: s.method,
      description: s.description,
      configSchema: s.configSchema,
    }))
  },

  getConfiguration(): AuthConfiguration {
    return authConfiguration.get()
  },

  updateConfiguration(updates: Partial<AuthConfiguration>): void {
    authConfiguration.update(updates)
  },

  getAnalytics(): AuthAnalytics {
    return getAuthAnalytics()
  },

  attachBrowser(authSessionId: string, providerId: string, browserId: string): BrowserAttachment {
    return authBrowserIntegration.attachSession(authSessionId, providerId, browserId)
  },

  detachBrowser(authSessionId: string, providerId: string): void {
    authBrowserIntegration.detachSession(authSessionId, providerId)
  },

  on<E extends keyof AuthEventPayload>(event: E, listener: (payload: AuthEventPayload[E]) => void): () => void {
    return authEventEmitter.on(event as any, listener as any)
  },
}
