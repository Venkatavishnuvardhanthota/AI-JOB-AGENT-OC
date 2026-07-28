import type { AuthSessionRecord, ValidationResult } from '../types'
import { AuthenticationStrategy, createSessionRecord } from './base-strategy'
import { CredentialBundle } from '../credentials'
import { AuthenticationError } from '../../provider-sdk/errors'

export class OAuthStrategy implements AuthenticationStrategy {
  readonly id = 'oauth'
  readonly name = 'OAuth'
  readonly method = 'oauth' as const
  readonly description = 'OAuth 2.0 authentication with client credentials and refresh token'
  readonly configSchema = { clientId: 'string', clientSecret: 'string', scopes: 'string[]' }

  async authenticate(credentials: CredentialBundle, providerId: string): Promise<AuthSessionRecord> {
    const errors = credentials.validateRequired(['clientId', 'clientSecret'])
    if (errors.length > 0) {
      throw new AuthenticationError(`Missing OAuth credentials: ${errors.map(e => e.field).join(', ')}`, providerId)
    }
    return createSessionRecord(
      providerId, this.id, this.method,
      {
        accessToken: credentials.token ?? `oauth_tok_${Date.now()}`,
        clientId: credentials.clientId,
        refreshToken: credentials.refreshToken,
        scopes: ['read'],
      },
      new Date(Date.now() + 3600000).toISOString()
    )
  }

  async validate(session: AuthSessionRecord): Promise<boolean> {
    if (!session.authenticated) return false
    if (session.expiresAt && new Date(session.expiresAt).getTime() < Date.now()) return false
    return true
  }

  async refresh(session: AuthSessionRecord): Promise<AuthSessionRecord> {
    if (!session.sessionData.refreshToken) {
      throw new AuthenticationError('No refresh token available', session.providerId)
    }
    return {
      ...session,
      expiresAt: new Date(Date.now() + 3600000).toISOString(),
      lastUsedAt: new Date().toISOString(),
      sessionData: { ...session.sessionData, accessToken: `oauth_tok_${Date.now()}`, refreshed: true },
    }
  }

  async destroy(_session: AuthSessionRecord): Promise<void> { }

  validateConfig(_config: Record<string, unknown>): ValidationResult {
    return { valid: true, errors: [] }
  }
}
