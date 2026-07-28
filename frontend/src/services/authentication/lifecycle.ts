import type { AuthLifecycleState } from './types'

const VALID_TRANSITIONS: Record<AuthLifecycleState, AuthLifecycleState[]> = {
  created: ['authenticating', 'destroyed'],
  authenticating: ['authenticated', 'failed', 'destroyed'],
  authenticated: ['validating', 'refreshing', 'expired', 'logged_out', 'destroyed'],
  validating: ['authenticated', 'expired', 'failed', 'destroyed'],
  refreshing: ['authenticated', 'failed', 'expired', 'destroyed'],
  expired: ['authenticating', 'logged_out', 'destroyed'],
  logged_out: ['authenticated', 'destroyed'],
  failed: ['authenticating', 'destroyed'],
  destroyed: [],
}

export class AuthLifecycle {
  private _state: AuthLifecycleState = 'created'
  private listeners: Array<{ from: AuthLifecycleState; to: AuthLifecycleState; timestamp: string }> = []

  get state(): AuthLifecycleState {
    return this._state
  }

  transition(to: AuthLifecycleState): void {
    const from = this._state
    const allowed = VALID_TRANSITIONS[from]
    if (!allowed.includes(to)) {
      throw new Error(`Invalid lifecycle transition: ${from} -> ${to}`)
    }
    this._state = to
    this.listeners.push({ from, to, timestamp: new Date().toISOString() })
  }

  canTransitionTo(state: AuthLifecycleState): boolean {
    return VALID_TRANSITIONS[this._state].includes(state)
  }

  getHistory(): Array<{ from: AuthLifecycleState; to: AuthLifecycleState; timestamp: string }> {
    return [...this.listeners]
  }

  reset(): void {
    this._state = 'created'
    this.listeners = []
  }

  static isValidTransition(from: AuthLifecycleState, to: AuthLifecycleState): boolean {
    return VALID_TRANSITIONS[from]?.includes(to) ?? false
  }

  static getAvailableTransitions(state: AuthLifecycleState): AuthLifecycleState[] {
    return [...(VALID_TRANSITIONS[state] ?? [])]
  }
}
