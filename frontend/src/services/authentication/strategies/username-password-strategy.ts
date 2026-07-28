import type { AuthSessionRecord, ValidationResult } from '../types'
import { AuthenticationStrategy, createSessionRecord } from './base-strategy'
import { CredentialBundle } from '../credentials'
import { AuthenticationError } from '../../provider-sdk/errors'

export class UsernamePasswordStrategy implements AuthenticationStrategy {
  readonly id = 'username_password'
  readonly name = 'Username / Password'
  readonly method = 'username_password' as const
  readonly description = 'Traditional username and password authentication'
  readonly configSchema = { username: 'string', password: 'string', rememberMe: 'boolean' }

  async authenticate(credentials: CredentialBundle, providerId: string): Promise<AuthSessionRecord> {
    const errors = credentials.validateRequired(['username', 'password'])
    if (errors.length > 0) {
      throw new AuthenticationError(`Missing credentials: ${errors.map(e => e.field).join(', ')}`, providerId)
    }
    return createSessionRecord(
      providerId, this.id, this.method,
      { username: credentials.username, authenticatedAt: new Date().toISOString() },
      new Date(Date.now() + 43200000).toISOString()
    )
  }

  async validate(session: AuthSessionRecord): Promise<boolean> {
    if (!session.authenticated) return false
    if (session.expiresAt && new Date(session.expiresAt).getTime() < Date.now()) return false
    return true
  }

  async refresh(session: AuthSessionRecord): Promise<AuthSessionRecord> {
    return {
      ...session,
      expiresAt: new Date(Date.now() + 43200000).toISOString(),
      lastUsedAt: new Date().toISOString(),
      sessionData: { ...session.sessionData, refreshed: true },
    }
  }

  async destroy(_session: AuthSessionRecord): Promise<void> { }

  validateConfig(_config: Record<string, unknown>): ValidationResult {
    return { valid: true, errors: [] }
  }
}
