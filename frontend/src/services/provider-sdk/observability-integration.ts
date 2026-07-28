import type { ProviderContext, ProviderMetadata, ProviderHealthCheckResult, CapabilityId } from './types'
import { observabilityService } from '../production/observability-service'
import { loggingService } from '../production/logging-service'
import { metricsService, recordProviderLatency } from '../production/metrics-service'
import { alertService, raiseProviderFailure } from '../production/alert-service'
import { healthService } from '../production/health-service'
import type { ServiceName } from '../production/production-types'

function toServiceName(_providerId: string): ServiceName {
  return 'discovery-engine'
}

export function createObservabilityContext(providerId: string, overrides?: Partial<ProviderContext>): ProviderContext {
  const ctx = observabilityService.createContext({ providerId })
  return {
    correlationId: ctx.correlationId,
    requestId: ctx.requestId ?? '',
    providerId,
    config: {},
    startTime: Date.now(),
    metadata: {},
    ...overrides,
  }
}

export function emitProviderMetrics(
  providerId: string,
  operation: string,
  durationMs: number,
  success: boolean,
  tags?: Record<string, string>
): void {
  metricsService.record(`provider.${providerId}.${operation}`, durationMs, 'ms', {
    provider: providerId,
    operation,
    success: String(success),
    ...tags,
  }, toServiceName(providerId))

  if (operation === 'search') {
    recordProviderLatency(providerId, durationMs)
  }
}

export function emitProviderLog(
  providerId: string,
  level: 'debug' | 'info' | 'warn' | 'error',
  message: string,
  _context?: Partial<ProviderContext>,
  data?: Record<string, unknown>
): void {
  const ctx = observabilityService.createContext({ providerId })
  switch (level) {
    case 'debug':
      loggingService.debug(`[${providerId}] ${message}`, ctx, data, toServiceName(providerId))
      break
    case 'info':
      loggingService.info(`[${providerId}] ${message}`, ctx, data, toServiceName(providerId))
      break
    case 'warn':
      loggingService.warn(`[${providerId}] ${message}`, ctx, data, toServiceName(providerId))
      break
    case 'error':
      loggingService.error(`[${providerId}] ${message}`, undefined, ctx, data, toServiceName(providerId))
      break
  }
}

export function emitProviderAlert(
  providerId: string,
  severity: 'info' | 'warning' | 'error' | 'critical',
  title: string,
  message: string,
  metadata?: Record<string, unknown>
): void {
  alertService.raise(title, message, severity, toServiceName(providerId), `provider:${providerId}`, {
    providerId,
    ...metadata,
  })
}

export function trackProviderHealth(
  providerId: string,
  result: ProviderHealthCheckResult
): void {
  healthService.updateStatus({
    service: toServiceName(providerId),
    status: result.status,
    lastCheck: result.lastCheck,
    responseTime: result.latency,
    uptime: result.status === 'healthy' ? 100 : result.status === 'degraded' ? 50 : 0,
    errorCount: result.status === 'unhealthy' ? 1 : 0,
    message: result.message ?? `${providerId} health: ${result.status}`,
    details: result.details,
  })

  if (result.status === 'unhealthy') {
    raiseProviderFailure(providerId, result.message ?? 'Health check failed')
  }
}

export function wrapWithObservability<T>(
  providerId: string,
  operation: string,
  fn: (ctx: ProviderContext) => Promise<T>,
  context?: Partial<ProviderContext>
): Promise<T> {
  const ctx = createObservabilityContext(providerId, context)
  const span = observabilityService.startSpan(`provider.${providerId}.${operation}`, observabilityService.createContext({ providerId }))

  return fn(ctx)
    .then((result) => {
      const duration = observabilityService.endSpan(span)
      emitProviderMetrics(providerId, operation, duration, true)
      emitProviderLog(providerId, 'info', `${operation} completed in ${duration}ms`, ctx)
      return result
    })
    .catch((error: Error) => {
      const duration = observabilityService.endSpan(span)
      emitProviderMetrics(providerId, operation, duration, false, { error: error.message })
      emitProviderLog(providerId, 'error', `${operation} failed: ${error.message}`, ctx, { error: error.message })
      emitProviderAlert(providerId, 'error', `Provider ${operation} Error`, `${providerId} ${operation}: ${error.message}`, { operation, error: error.message })
      throw error
    })
}

export function initializeProviderObservability(metadata: ProviderMetadata): void {
  emitProviderLog(metadata.id, 'info', `Provider registered: ${metadata.name} v${metadata.version}`, undefined, {
    capabilities: metadata.capabilities,
    authMethods: metadata.authMethods,
  })

  metricsService.record(`provider.registered`, 1, 'count', { provider: metadata.id }, toServiceName(metadata.id))
}

export function trackProviderCapabilityUsage(providerId: string, capability: CapabilityId, durationMs: number, success: boolean): void {
  metricsService.record(`provider.${providerId}.capability.${capability}`, durationMs, 'ms', {
    provider: providerId,
    capability,
    success: String(success),
  }, toServiceName(providerId))
}
