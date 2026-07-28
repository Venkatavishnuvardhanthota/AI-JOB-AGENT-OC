import type { Alert, AlertSeverity, ServiceName } from './production-types'
import { v4Service, nowISO } from '../orchestration/utils'
import { loggingService } from './logging-service'

const PREFIX = 'ajapp_alert_'

function get<T>(key: string, fallback: T): T {
  try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback } catch { return fallback }
}
function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

function createAlert(title: string, message: string, severity: AlertSeverity, service: ServiceName, source: string, metadata?: Record<string, unknown>): Alert {
  return {
    id: v4Service.generate('alert'),
    title,
    message,
    severity,
    status: 'active',
    service,
    source,
    timestamp: nowISO(),
    metadata,
  }
}

export const alertService = {
  raise(title: string, message: string, severity: AlertSeverity, service: ServiceName, source: string, metadata?: Record<string, unknown>): Alert {
    const alert = createAlert(title, message, severity, service, source, metadata)
    const alerts = this.getAll()
    alerts.unshift(alert)
    set(PREFIX + 'alerts', alerts.slice(0, 500))

    loggingService.warn(`Alert [${severity}] ${title}: ${message}`, undefined, { alertId: alert.id, service, source }, service)

    if (severity === 'critical') {
      loggingService.error(`CRITICAL ALERT: ${title}`, undefined, undefined, { alertId: alert.id, ...metadata }, service)
    }

    return alert
  },

  acknowledge(id: string): Alert | null {
    const alerts = this.getAll()
    const alert = alerts.find(a => a.id === id)
    if (alert && alert.status === 'active') {
      alert.status = 'acknowledged'
      alert.acknowledgedAt = nowISO()
      set(PREFIX + 'alerts', alerts)
    }
    return alert ?? null
  },

  resolve(id: string): Alert | null {
    const alerts = this.getAll()
    const alert = alerts.find(a => a.id === id)
    if (alert && (alert.status === 'active' || alert.status === 'acknowledged')) {
      alert.status = 'resolved'
      alert.resolvedAt = nowISO()
      set(PREFIX + 'alerts', alerts)
    }
    return alert ?? null
  },

  suppress(id: string): Alert | null {
    const alerts = this.getAll()
    const alert = alerts.find(a => a.id === id)
    if (alert) {
      alert.status = 'suppressed'
      set(PREFIX + 'alerts', alerts)
    }
    return alert ?? null
  },

  getAll(): Alert[] {
    return get<Alert[]>(PREFIX + 'alerts', [])
  },

  getActive(): Alert[] {
    return this.getAll().filter(a => a.status === 'active')
  },

  getBySeverity(severity: AlertSeverity): Alert[] {
    return this.getAll().filter(a => a.severity === severity)
  },

  getByService(service: ServiceName): Alert[] {
    return this.getAll().filter(a => a.service === service)
  },

  getRecent(count: number = 50): Alert[] {
    return this.getAll().slice(0, count)
  },

  getCriticalUnresolved(): Alert[] {
    return this.getAll().filter(a => a.severity === 'critical' && (a.status === 'active' || a.status === 'acknowledged'))
  },

  getAlertCounts(): { active: number; acknowledged: number; resolved: number; suppressed: number; total: number } {
    const alerts = this.getAll()
    return {
      active: alerts.filter(a => a.status === 'active').length,
      acknowledged: alerts.filter(a => a.status === 'acknowledged').length,
      resolved: alerts.filter(a => a.status === 'resolved').length,
      suppressed: alerts.filter(a => a.status === 'suppressed').length,
      total: alerts.length,
    }
  },

  clearResolved(): void {
    set(PREFIX + 'alerts', this.getAll().filter(a => a.status !== 'resolved'))
  },

  clearAll(): void {
    set(PREFIX + 'alerts', [])
  },
}

export function raiseHighErrorRate(errorRate: number, threshold: number, service: ServiceName): void {
  alertService.raise(
    'High Error Rate',
    `${service} error rate is ${errorRate.toFixed(1)}% (threshold: ${threshold}%)`,
    errorRate > threshold * 1.5 ? 'critical' : 'error',
    service,
    'health-monitor',
    { errorRate, threshold }
  )
}

export function raiseWorkflowFailure(workflowId: string, jobTitle: string, company: string): void {
  alertService.raise(
    'Workflow Failure',
    `Workflow for ${jobTitle} at ${company} (${workflowId}) has failed`,
    'error',
    'workflow-engine',
    'workflow-orchestrator',
    { workflowId, jobTitle, company }
  )
}

export function raiseBrowserCrash(browserId: string): void {
  alertService.raise(
    'Browser Crash',
    `Browser session ${browserId} has crashed`,
    'critical',
    'browser-framework',
    'browser-monitor',
    { browserId }
  )
}

export function raiseQueueBacklog(depth: number, threshold: number): void {
  alertService.raise(
    'Queue Backlog',
    `Queue depth is ${depth} (threshold: ${threshold})`,
    depth > threshold * 2 ? 'critical' : 'warning',
    'queue-system',
    'queue-monitor',
    { depth, threshold }
  )
}

export function raiseRetryStorm(count: number, windowMinutes: number): void {
  alertService.raise(
    'Retry Storm',
    `${count} retries in the last ${windowMinutes} minutes`,
    'warning',
    'workflow-engine',
    'retry-monitor',
    { count, windowMinutes }
  )
}

export function raiseProviderFailure(provider: string, error: string): void {
  alertService.raise(
    'Provider Failure',
    `Provider ${provider} failed: ${error}`,
    'error',
    'discovery-engine',
    'provider-monitor',
    { provider, error }
  )
}

export function raiseSlowResponse(operation: string, duration: number, threshold: number): void {
  alertService.raise(
    'Slow Response',
    `${operation} took ${duration}ms (threshold: ${threshold}ms)`,
    'warning',
    'workflow-engine',
    'performance-monitor',
    { operation, duration, threshold }
  )
}
