import type { LifecycleState, ProviderContext, AuthSession, AuthCredentials } from './types'
import { ProviderError } from './errors'
import { createAuthProvider, type AuthProvider } from './auth-abstraction'
import type { AuthMethodType } from './types'
import { observabilityService } from '../production/observability-service'
import { v4Service } from '../orchestration/utils'

export class ProviderLifecycle {
  private state: LifecycleState = 'created'
  private authProvider: AuthProvider | null = null
  private authSession: AuthSession | null = null
  private eventListeners: Map<string, Array<(...args: unknown[]) => void>> = new Map()

  constructor(private providerId: string) {}

  get currentState(): LifecycleState {
    return this.state
  }

  on(event: string, listener: (...args: unknown[]) => void): void {
    const listeners = this.eventListeners.get(event) ?? []
    listeners.push(listener)
    this.eventListeners.set(event, listeners)
  }

  private emit(event: string, ...args: unknown[]): void {
    const listeners = this.eventListeners.get(event)
    if (listeners) {
      for (const listener of listeners) listener(...args)
    }
  }

  private transition(to: LifecycleState): void {
    const from = this.state
    this.state = to
    this.emit('stateChange', { from, to, providerId: this.providerId })
  }

  async initialize(config: Record<string, unknown>): Promise<ProviderContext> {
    if (this.state !== 'created') {
      throw new ProviderError(`Cannot initialize from state ${this.state}`, 'INVALID_LIFECYCLE', this.providerId)
    }
    const ctx: ProviderContext = {
      correlationId: observabilityService.getCorrelationId(),
      requestId: v4Service.generate('req'),
      providerId: this.providerId,
      config,
      startTime: Date.now(),
      metadata: {},
    }
    this.transition('initialized')
    this.emit('initialized', { providerId: this.providerId, config })
    return ctx
  }

  async authenticate(credentials: AuthCredentials, authMethods: AuthMethodType[]): Promise<AuthSession> {
    if (this.state !== 'initialized' && this.state !== 'active') {
      throw new ProviderError(`Cannot authenticate from state ${this.state}`, 'INVALID_LIFECYCLE', this.providerId)
    }
    if (authMethods.length === 0) {
      this.transition('active')
      return { method: 'credentials' as AuthMethodType, authenticated: false, expiresAt: null, sessionData: {} }
    }
    const method = authMethods[0]
    this.authProvider = createAuthProvider(method)
    this.authSession = await this.authProvider.authenticate(credentials)
    this.transition('authenticated')

    if (this.authSession.authenticated) {
      await this.activate()
    }
    this.emit('authenticated', { providerId: this.providerId, method })
    return this.authSession
  }

  async activate(): Promise<void> {
    if (this.state !== 'authenticated' && this.state !== 'initialized') {
      throw new ProviderError(`Cannot activate from state ${this.state}`, 'INVALID_LIFECYCLE', this.providerId)
    }
    this.transition('active')
    this.emit('activated', { providerId: this.providerId })
  }

  async validateSession(): Promise<boolean> {
    if (!this.authProvider || !this.authSession) return false
    const valid = await this.authProvider.validateSession(this.authSession)
    if (!valid && this.authSession.authenticated) {
      try {
        this.authSession = await this.authProvider.refreshSession(this.authSession)
        return true
      } catch {
        return false
      }
    }
    return valid
  }

  async logout(): Promise<void> {
    if (this.authProvider && this.authSession) {
      await this.authProvider.logout(this.authSession)
    }
    this.authProvider = null
    this.authSession = null
    this.transition('initialized')
    this.emit('loggedOut', { providerId: this.providerId })
  }

  async cleanup(): Promise<void> {
    if (this.authProvider && this.authSession) {
      await this.authProvider.logout(this.authSession)
    }
    this.authProvider = null
    this.authSession = null
    this.transition('cleaned_up')
    this.emit('cleanedUp', { providerId: this.providerId })
  }

  onStateChange(callback: (from: LifecycleState, to: LifecycleState) => void): () => void {
    const handler = (event: unknown) => {
      const { from, to } = event as { from: LifecycleState; to: LifecycleState }
      callback(from, to)
    }
    this.on('stateChange', handler)
    return () => {
      const listeners = this.eventListeners.get('stateChange') ?? []
      const idx = listeners.indexOf(handler)
      if (idx !== -1) listeners.splice(idx, 1)
    }
  }
}
