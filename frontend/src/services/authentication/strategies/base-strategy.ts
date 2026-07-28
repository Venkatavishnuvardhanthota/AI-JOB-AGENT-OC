import type { AuthMethodType, AuthSessionRecord, ValidationResult, StrategyDescriptor } from '../types'
import { CredentialBundle } from '../credentials'

export interface AuthenticationStrategy {
  readonly id: string
  readonly name: string
  readonly method: AuthMethodType
  readonly description: string
  readonly configSchema: Record<string, unknown>

  authenticate(credentials: CredentialBundle, providerId: string): Promise<AuthSessionRecord>
  validate(session: AuthSessionRecord): Promise<boolean>
  refresh(session: AuthSessionRecord): Promise<AuthSessionRecord>
  destroy(session: AuthSessionRecord): Promise<void>
  validateConfig(config: Record<string, unknown>): ValidationResult
}

export function createSessionRecord(
  providerId: string,
  strategyId: string,
  method: AuthMethodType,
  sessionData: Record<string, unknown>,
  expiresAt: string | null
): AuthSessionRecord {
  return {
    id: `auth_sess_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    providerId,
    strategyId,
    method,
    authenticated: true,
    createdAt: new Date().toISOString(),
    expiresAt,
    lastUsedAt: new Date().toISOString(),
    sessionData,
    metadata: {},
  }
}

export function getDescriptor(strategy: AuthenticationStrategy): StrategyDescriptor {
  return {
    id: strategy.id,
    name: strategy.name,
    method: strategy.method,
    description: strategy.description,
    configSchema: strategy.configSchema,
  }
}
