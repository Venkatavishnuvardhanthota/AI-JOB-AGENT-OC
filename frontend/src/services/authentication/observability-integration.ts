import type { AuthAnalytics } from './types'
import { observabilityService } from '../production/observability-service'
import { loggingService } from '../production/logging-service'
import { metricsService } from '../production/metrics-service'
import { authSessionManager } from './auth-session-manager'

export function emitAuthLog(
  providerId: string,
  level: 'debug' | 'info' | 'warn' | 'error',
  message: string,
  data?: Record<string, unknown>
): void {
  const ctx = observabilityService.createContext({ providerId })
  const svc = 'discovery-engine' as const
  switch (level) {
    case 'debug': loggingService.debug(`[auth:${providerId}] ${message}`, ctx, data, svc); break
    case 'info': loggingService.info(`[auth:${providerId}] ${message}`, ctx, data, svc); break
    case 'warn': loggingService.warn(`[auth:${providerId}] ${message}`, ctx, data, svc); break
    case 'error': loggingService.error(`[auth:${providerId}] ${message}`, undefined, ctx, data, svc); break
  }
}

export function recordAuthMetric(name: string, value: number, tags?: Record<string, string>): void {
  metricsService.record(`auth.${name}`, value, 'count', { ...tags }, 'discovery-engine')
}

export function recordAuthDuration(name: string, durationMs: number, tags?: Record<string, string>): void {
  metricsService.recordDuration(`auth.${name}`, durationMs, { ...tags }, 'discovery-engine')
}

export function getAuthAnalytics(): AuthAnalytics {
  const all = authSessionManager.listAll()
  const active = authSessionManager.getActive()
  const expired = authSessionManager.getExpired()
  const totalAuthentications = all.length
  const failedAuthentications = all.filter(s => !s.authenticated).length
  const durations = all
    .filter(s => s.expiresAt && s.createdAt)
    .map(s => new Date(s.expiresAt!).getTime() - new Date(s.createdAt).getTime())
  const avgDuration = durations.length > 0 ? Math.round(durations.reduce((a, b) => a + b, 0) / durations.length) : 0
  const lastAuth = all.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())[0]

  return {
    totalAuthentications,
    successfulAuthentications: totalAuthentications - failedAuthentications,
    failedAuthentications,
    activeSessions: active.length,
    expiredSessions: expired.length,
    averageSessionDurationMs: avgDuration,
    lastAuthenticationAt: lastAuth?.createdAt ?? null,
  }
}
