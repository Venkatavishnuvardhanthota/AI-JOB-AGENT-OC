import type { AuthSessionRecord, ValidationResult } from '../types'
import { AuthenticationStrategy, createSessionRecord } from './base-strategy'
import { CredentialBundle } from '../credentials'
import { AuthenticationError } from '../../provider-sdk/errors'

export class ApiKeyStrategy implements AuthenticationStrategy {
  readonly id = 'api_key'
  readonly name = 'API Key'
  readonly method = 'api_key' as const
  readonly description = 'API key-based authentication for programmatic access'
  readonly configSchema = { apiKey: 'string', keyName: 'string' }

  async authenticate(credentials: CredentialBundle, providerId: string): Promise<AuthSessionRecord> {
    const errors = credentials.validateRequired(['apiKey'])
    if (errors.length > 0) {
      throw new AuthenticationError('Missing API key', providerId)
    }
    return createSessionRecord(
      providerId, this.id, this.method,
      { keyPrefix: credentials.apiKey!.substring(0, 8), keyName: credentials.getString('keyName') ?? 'default' },
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
