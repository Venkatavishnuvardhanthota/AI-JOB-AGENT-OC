import type { AuthSessionRecord, ValidationResult } from '../types'
import { AuthenticationStrategy, createSessionRecord } from './base-strategy'
import { CredentialBundle } from '../credentials'
import { AuthenticationError } from '../../provider-sdk/errors'

export class CookiesStrategy implements AuthenticationStrategy {
  readonly id = 'cookies'
  readonly name = 'Cookies'
  readonly method = 'cookies' as const
  readonly description = 'Cookie-based authentication using session cookies'
  readonly configSchema = { sessionCookie: 'string', domain: 'string' }

  async authenticate(credentials: CredentialBundle, providerId: string): Promise<AuthSessionRecord> {
    const errors = credentials.validateRequired(['sessionCookie'])
    if (errors.length > 0) {
      throw new AuthenticationError('Missing session cookie', providerId)
    }
    return createSessionRecord(
      providerId, this.id, this.method,
      { cookie: credentials.sessionCookie, domain: credentials.getString('domain') ?? 'unknown' },
      new Date(Date.now() + 86400000).toISOString()
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
      expiresAt: new Date(Date.now() + 86400000).toISOString(),
      lastUsedAt: new Date().toISOString(),
    }
  }

  async destroy(_session: AuthSessionRecord): Promise<void> { }

  validateConfig(_config: Record<string, unknown>): ValidationResult {
    return { valid: true, errors: [] }
  }
}
