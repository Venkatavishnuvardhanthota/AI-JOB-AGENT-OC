import type { AuthSessionRecord, ValidationResult } from '../types'
import { AuthenticationStrategy, createSessionRecord } from './base-strategy'
import { CredentialBundle } from '../credentials'
import { AuthenticationError } from '../../provider-sdk/errors'

export class SessionTokenStrategy implements AuthenticationStrategy {
  readonly id = 'session_token'
  readonly name = 'Session Token'
  readonly method = 'session_token' as const
  readonly description = 'Token-based authentication using session tokens'
  readonly configSchema = { token: 'string' }

  async authenticate(credentials: CredentialBundle, providerId: string): Promise<AuthSessionRecord> {
    const errors = credentials.validateRequired(['token'])
    if (errors.length > 0) {
      throw new AuthenticationError('Missing session token', providerId)
    }
    return createSessionRecord(
      providerId, this.id, this.method,
      { token: credentials.token, tokenPrefix: credentials.token!.substring(0, 8) },
      new Date(Date.now() + 7200000).toISOString()
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
      expiresAt: new Date(Date.now() + 7200000).toISOString(),
      lastUsedAt: new Date().toISOString(),
      sessionData: { ...session.sessionData, refreshed: true },
    }
  }

  async destroy(_session: AuthSessionRecord): Promise<void> { }

  validateConfig(_config: Record<string, unknown>): ValidationResult {
    return { valid: true, errors: [] }
  }
}
