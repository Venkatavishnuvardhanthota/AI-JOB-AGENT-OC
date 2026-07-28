import type { AuthSessionRecord, ValidationResult } from '../types'
import { AuthenticationStrategy, createSessionRecord } from './base-strategy'
import { CredentialBundle } from '../credentials'

export class AnonymousStrategy implements AuthenticationStrategy {
  readonly id = 'anonymous'
  readonly name = 'Anonymous'
  readonly method = 'anonymous' as const
  readonly description = 'Anonymous access with no authentication required'
  readonly configSchema = {}

  async authenticate(_credentials: CredentialBundle, providerId: string): Promise<AuthSessionRecord> {
    return createSessionRecord(
      providerId, this.id, this.method,
      { anonymous: true, sessionTag: `anon_${Date.now()}` },
      null
    )
  }

  async validate(_session: AuthSessionRecord): Promise<boolean> {
    return true
  }

  async refresh(session: AuthSessionRecord): Promise<AuthSessionRecord> {
    return { ...session, lastUsedAt: new Date().toISOString() }
  }

  async destroy(_session: AuthSessionRecord): Promise<void> { }

  validateConfig(_config: Record<string, unknown>): ValidationResult {
    return { valid: true, errors: [] }
  }
}
