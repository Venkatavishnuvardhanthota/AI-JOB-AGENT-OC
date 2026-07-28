export type AuthMethodType = 'oauth' | 'username_password' | 'cookies' | 'session_token' | 'browser_session' | 'api_key' | 'anonymous' | 'custom'

export type AuthLifecycleState =
  | 'created'
  | 'authenticating'
  | 'authenticated'
  | 'validating'
  | 'refreshing'
  | 'expired'
  | 'logged_out'
  | 'failed'
  | 'destroyed'

export type AuthEventType =
  | 'authentication_started'
  | 'authentication_succeeded'
  | 'authentication_failed'
  | 'session_refreshed'
  | 'session_expired'
  | 'session_destroyed'
  | 'strategy_registered'
  | 'strategy_unregistered'

export type StorageType = 'memory' | 'encrypted' | 'environment' | 'browser' | 'secret_manager'

export interface AuthEventPayload {
  authentication_started: { providerId: string; strategyId: string; timestamp: string }
  authentication_succeeded: { providerId: string; strategyId: string; sessionId: string; timestamp: string }
  authentication_failed: { providerId: string; strategyId: string; error: string; timestamp: string }
  session_refreshed: { providerId: string; sessionId: string; timestamp: string }
  session_expired: { providerId: string; sessionId: string; timestamp: string }
  session_destroyed: { providerId: string; sessionId: string; timestamp: string }
  strategy_registered: { strategyId: string; method: AuthMethodType; timestamp: string }
  strategy_unregistered: { strategyId: string; timestamp: string }
}

export interface AuthSessionRecord {
  id: string
  providerId: string
  strategyId: string
  method: AuthMethodType
  authenticated: boolean
  createdAt: string
  expiresAt: string | null
  lastUsedAt: string
  sessionData: Record<string, unknown>
  metadata: Record<string, unknown>
}

export interface AuthConfiguration {
  sessionTimeoutMs: number
  refreshEnabled: boolean
  refreshThresholdMs: number
  maxRetries: number
  retryDelayMs: number
  storageType: StorageType
  validateOnResume: boolean
  maxConcurrentSessions: number
}

export const DEFAULT_AUTH_CONFIGURATION: AuthConfiguration = {
  sessionTimeoutMs: 3600000,
  refreshEnabled: true,
  refreshThresholdMs: 300000,
  maxRetries: 3,
  retryDelayMs: 1000,
  storageType: 'memory',
  validateOnResume: true,
  maxConcurrentSessions: 5,
}

export interface ValidationResult {
  valid: boolean
  errors: ValidationError[]
}

export interface ValidationError {
  field: string
  message: string
  code: string
}

export interface StrategyDescriptor {
  id: string
  name: string
  method: AuthMethodType
  description: string
  configSchema: Record<string, unknown>
}

export interface BrowserAttachment {
  browserId: string
  sessionId: string
  attachedAt: string
  cookiesImported: boolean
  cookiesExported: boolean
  profileReused: boolean
}

export interface AuthAnalytics {
  totalAuthentications: number
  successfulAuthentications: number
  failedAuthentications: number
  activeSessions: number
  expiredSessions: number
  averageSessionDurationMs: number
  lastAuthenticationAt: string | null
}
