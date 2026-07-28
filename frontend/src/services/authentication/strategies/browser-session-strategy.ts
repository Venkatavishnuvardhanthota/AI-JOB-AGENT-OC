import type { AuthSessionRecord, ValidationResult } from '../types'
import { AuthenticationStrategy, createSessionRecord } from './base-strategy'
import { CredentialBundle } from '../credentials'

export class BrowserSessionStrategy implements AuthenticationStrategy {
  readonly id = 'browser_session'
  readonly name = 'Browser Session'
  readonly method = 'browser_session' as const
  readonly description = 'Authentication via browser session with cookies and storage state'
  readonly configSchema = { browserId: 'string', profileData: 'object' }

  async authenticate(credentials: CredentialBundle, providerId: string): Promise<AuthSessionRecord> {
    const session = createSessionRecord(
      providerId, this.id, this.method,
      {
        browserId: credentials.getString('browserId') ?? `br_${Date.now()}`,
        profileData: credentials.get('profileData') ?? {},
      },
      new Date(Date.now() + 1800000).toISOString()
    )
    return session
  }

  async validate(session: AuthSessionRecord): Promise<boolean> {
    if (!session.authenticated) return false
    if (session.expiresAt && new Date(session.expiresAt).getTime() < Date.now()) return false
    return true
  }

  async refresh(session: AuthSessionRecord): Promise<AuthSessionRecord> {
    return {
      ...session,
      expiresAt: new Date(Date.now() + 1800000).toISOString(),
      lastUsedAt: new Date().toISOString(),
    }
  }

  async destroy(_session: AuthSessionRecord): Promise<void> { }

  validateConfig(_config: Record<string, unknown>): ValidationResult {
    return { valid: true, errors: [] }
  }
}
