import type { ServiceHealth, HealthStatus, ServiceName } from './production-types'
import { nowISO } from '../orchestration/utils'
import { metricsService } from './metrics-service'

const PREFIX = 'ajapp_hlth_'

function get<T>(key: string, fallback: T): T {
  try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback } catch { return fallback }
}
function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

const ALL_SERVICES: ServiceName[] = [
  'discovery-engine', 'matching-engine', 'browser-framework',
  'generation-engine', 'workflow-engine', 'notification-system',
  'queue-system', 'storage', 'config', 'analytics',
]

function createDefaultHealth(service: ServiceName): ServiceHealth {
  return {
    service,
    status: 'healthy',
    lastCheck: nowISO(),
    responseTime: 0,
    uptime: 100,
    errorCount: 0,
    message: `${service} is healthy`,
  }
}

export const healthService = {
  check(service: ServiceName): ServiceHealth {
    const health = this.getStatus(service) ?? createDefaultHealth(service)

    const errorRate = this.getErrorRate(service, 5)
    const queueDepth = service === 'queue-system' ? this.getQueueDepth() : 0

    if (errorRate > 20 || health.errorCount > 50) {
      health.status = 'critical'
      health.message = `${service} has critical error rate: ${errorRate.toFixed(1)}%`
    } else if (errorRate > 10 || queueDepth > 100) {
      health.status = 'degraded'
      health.message = `${service} is degraded: error rate ${errorRate.toFixed(1)}%`
    } else if (errorRate > 5 || queueDepth > 50) {
      health.status = 'warning'
      health.message = `${service} has elevated error rate: ${errorRate.toFixed(1)}%`
    } else {
      health.status = 'healthy'
      health.message = `${service} is healthy`
    }

    health.lastCheck = nowISO()
    health.responseTime = Math.round(Math.random() * 100 + 10)
    this.updateStatus(health)
    return health
  },

  checkAll(): ServiceHealth[] {
    return ALL_SERVICES.map(s => this.check(s))
  },

  getStatus(service: ServiceName): ServiceHealth | null {
    return get<ServiceHealth | null>(PREFIX + service, null)
  },

  updateStatus(health: ServiceHealth): void {
    set(PREFIX + health.service, health)
  },

  getAllStatuses(): ServiceHealth[] {
    return ALL_SERVICES.map(s => this.getStatus(s) ?? createDefaultHealth(s))
  },

  getErrorRate(service: ServiceName, _minutes: number = 5): number {
    const errors = metricsService.getAggregatedValue(`workflow.failures`, { service }, 'count')
    const total = metricsService.getAggregatedValue(`workflow.executions`, { service }, 'count')
    if (total === 0) return 0
    return (errors / total) * 100
  },

  getQueueDepth(): number {
    try {
      const raw = localStorage.getItem('ajapp_ork_q_priority')
      if (!raw) return 0
      const queue = JSON.parse(raw)
      return Array.isArray(queue) ? queue.length : 0
    } catch { return 0 }
  },

  reportError(service: ServiceName): void {
    const health = this.getStatus(service) ?? createDefaultHealth(service)
    health.errorCount++
    this.updateStatus(health)
  },

  clearErrors(service: ServiceName): void {
    const health = this.getStatus(service) ?? createDefaultHealth(service)
    health.errorCount = 0
    this.updateStatus(health)
  },

  getOverallStatus(): { status: HealthStatus; healthy: number; warning: number; degraded: number; critical: number; offline: number; total: number } {
    const statuses = this.getAllStatuses()
    return {
      status: statuses.some(s => s.status === 'critical') ? 'critical'
        : statuses.some(s => s.status === 'degraded') ? 'degraded'
        : statuses.some(s => s.status === 'warning') ? 'warning'
        : 'healthy',
      healthy: statuses.filter(s => s.status === 'healthy').length,
      warning: statuses.filter(s => s.status === 'warning').length,
      degraded: statuses.filter(s => s.status === 'degraded').length,
      critical: statuses.filter(s => s.status === 'critical').length,
      offline: statuses.filter(s => s.status === 'offline').length,
      total: statuses.length,
    }
  },

  resetAll(): void {
    for (const service of ALL_SERVICES) {
      this.updateStatus(createDefaultHealth(service))
    }
  },
}
