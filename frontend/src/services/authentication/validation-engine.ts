import type { AuthSessionRecord, AuthConfiguration, ValidationResult, AuthMethodType } from './types'
import { CredentialBundle } from './credentials'

export const validationEngine = {
  validateCredentials(credentials: CredentialBundle, method: AuthMethodType): ValidationResult {
    const errors = credentials.validateRequired(this.getRequiredFields(method))
    return { valid: errors.length === 0, errors }
  },

  validateSession(session: AuthSessionRecord): ValidationResult {
    const errors: { field: string; message: string; code: string }[] = []
    if (!session.id) errors.push({ field: 'id', message: 'Session ID is required', code: 'MISSING_SESSION_ID' })
    if (!session.providerId) errors.push({ field: 'providerId', message: 'Provider ID is required', code: 'MISSING_PROVIDER_ID' })
    if (!session.strategyId) errors.push({ field: 'strategyId', message: 'Strategy ID is required', code: 'MISSING_STRATEGY_ID' })
    if (session.expiresAt && new Date(session.expiresAt).getTime() <= Date.now()) {
      errors.push({ field: 'expiresAt', message: 'Session has expired', code: 'SESSION_EXPIRED' })
    }
    return { valid: errors.length === 0, errors }
  },

  validateConfiguration(config: Partial<AuthConfiguration>): ValidationResult {
    const errors: { field: string; message: string; code: string }[] = []
    if (config.sessionTimeoutMs !== undefined && config.sessionTimeoutMs < 60000) {
      errors.push({ field: 'sessionTimeoutMs', message: 'Session timeout must be at least 60000ms', code: 'INVALID_TIMEOUT' })
    }
    if (config.maxRetries !== undefined && config.maxRetries < 0) {
      errors.push({ field: 'maxRetries', message: 'Max retries cannot be negative', code: 'INVALID_RETRIES' })
    }
    if (config.maxConcurrentSessions !== undefined && config.maxConcurrentSessions < 1) {
      errors.push({ field: 'maxConcurrentSessions', message: 'Must allow at least 1 concurrent session', code: 'INVALID_CONCURRENT' })
    }
    return { valid: errors.length === 0, errors }
  },

  validatePolicy(config: AuthConfiguration): ValidationResult {
    const errors: { field: string; message: string; code: string }[] = []
    if (config.refreshEnabled && config.refreshThresholdMs >= config.sessionTimeoutMs) {
      errors.push({ field: 'refreshThresholdMs', message: 'Refresh threshold must be less than session timeout', code: 'INVALID_REFRESH_THRESHOLD' })
    }
    if (config.storageType === 'encrypted' && !('crypto' in globalThis)) {
      errors.push({ field: 'storageType', message: 'Encrypted storage requires crypto support', code: 'CRYPTO_UNAVAILABLE' })
    }
    return { valid: errors.length === 0, errors }
  },

  validateProvider(providerId: string, config: Record<string, unknown>): ValidationResult {
    const errors: { field: string; message: string; code: string }[] = []
    if (!providerId) errors.push({ field: 'providerId', message: 'Provider ID is required', code: 'MISSING_PROVIDER_ID' })
    if (!config || Object.keys(config).length === 0) {
      errors.push({ field: 'config', message: 'Provider configuration is required', code: 'MISSING_CONFIG' })
    }
    return { valid: errors.length === 0, errors }
  },

  getRequiredFields(method: AuthMethodType): string[] {
    switch (method) {
      case 'oauth': return ['clientId', 'clientSecret']
      case 'username_password': return ['username', 'password']
      case 'cookies': return ['sessionCookie']
      case 'session_token': return ['token']
      case 'browser_session': return ['browserId']
      case 'api_key': return ['apiKey']
      case 'anonymous': return []
      case 'custom': return []
    }
  },
}
