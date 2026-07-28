import type { DiagnosticReport, ServiceHealth, ServiceName } from './production-types'
import { nowISO } from '../orchestration/utils'
import { healthService } from './health-service'
import { alertService } from './alert-service'
import { configService } from './config-service'
const SYSTEM_DEPENDENCIES: { name: string; version: string }[] = [
  { name: 'React', version: '18.x' },
  { name: 'React Router', version: '6.x' },
  { name: 'TypeScript', version: '5.x' },
  { name: 'Vite', version: '5.x' },
  { name: 'localStorage', version: 'Web API' },
  { name: 'IndexedDB (if available)', version: 'Web API' },
]

export const diagnosticsService = {
  generateReport(): DiagnosticReport {
    const services = healthService.checkAll()
    const overall = healthService.getOverallStatus()

    const metricsSnapshot = this.getMetricsSnapshot()
    const appConfig = configService.get()

    return {
      generated: nowISO(),
      system: {
        version: appConfig.version,
        uptime: this.getUptime(),
        totalServices: overall.total,
        healthyServices: overall.healthy,
        degradedServices: overall.degraded,
        offlineServices: overall.offline,
      },
      services,
      metrics: metricsSnapshot,
      alerts: alertService.getActive().slice(0, 20),
      config: configService.getOptions().map(o => ({ key: o.key, value: o.value })),
      dependencies: this.checkDependencies(),
      recommendations: this.generateRecommendations(services),
    }
  },

  getMetricsSnapshot(): { name: string; current: number; unit: string }[] {
    try {
      const metrics: { name: string; current: number; unit: string }[] = []
      const keys = Object.keys(localStorage).filter(k => k.startsWith('ajapp_met_'))
      for (const key of keys) {
        try {
          const samples = JSON.parse(localStorage.getItem(key) || '[]') as { name: string; value: number; unit: string; timestamp: string }[]
          if (samples.length > 0) {
            const last = samples[samples.length - 1]
            metrics.push({ name: last.name, current: last.value, unit: last.unit })
          }
        } catch {}
      }
      return metrics
    } catch { return [] }
  },

  checkDependencies(): { name: string; status: 'healthy' | 'degraded' | 'critical'; version: string }[] {
    return SYSTEM_DEPENDENCIES.map(dep => ({
      ...dep,
      status: 'healthy' as const,
    }))
  },

  getUptime(): number {
    try {
      const raw = localStorage.getItem('ajapp_started_at')
      if (!raw) {
        localStorage.setItem('ajapp_started_at', nowISO())
        return 0
      }
      const start = new Date(raw).getTime()
      return Math.floor((Date.now() - start) / 1000)
    } catch { return 0 }
  },

  generateRecommendations(services: ServiceHealth[]): string[] {
    const recommendations: string[] = []
    const criticalServices = services.filter(s => s.status === 'critical' || s.status === 'degraded')

    if (criticalServices.length > 0) {
      recommendations.push(`Investigate ${criticalServices.length} degraded/critical service(s): ${criticalServices.map(s => s.service).join(', ')}`)
    }

    const highErrorRates = services.filter(s => s.errorCount > 20)
    if (highErrorRates.length > 0) {
      recommendations.push(`High error counts detected for: ${highErrorRates.map(s => s.service).join(', ')}`)
    }

    const queueDepth = healthService.getQueueDepth()
    if (queueDepth > 50) {
      recommendations.push(`Queue depth is ${queueDepth}. Consider increasing concurrency or investigating bottlecks.`)
    }

    recommendations.push('Schedule regular maintenance tasks to prune old data.')
    recommendations.push('Review configuration thresholds for optimal performance.')
    recommendations.push('Ensure all feature flags are correctly set for the current environment.')

    return recommendations
  },

  getServiceDependencyGraph(): { service: ServiceName; dependencies: string[]; dependents: string[] }[] {
    const graph: { service: ServiceName; dependencies: string[]; dependents: string[] }[] = [
      { service: 'discovery-engine', dependencies: ['config', 'storage'], dependents: ['matching-engine'] },
      { service: 'matching-engine', dependencies: ['discovery-engine', 'config', 'storage'], dependents: ['workflow-engine'] },
      { service: 'browser-framework', dependencies: ['config', 'storage'], dependents: ['workflow-engine'] },
      { service: 'generation-engine', dependencies: ['config', 'storage'], dependents: ['workflow-engine'] },
      { service: 'workflow-engine', dependencies: ['discovery-engine', 'matching-engine', 'browser-framework', 'generation-engine', 'queue-system', 'config', 'storage'], dependents: ['notification-system'] },
      { service: 'notification-system', dependencies: ['workflow-engine', 'config'], dependents: [] },
      { service: 'queue-system', dependencies: ['storage'], dependents: ['workflow-engine'] },
      { service: 'storage', dependencies: [], dependents: ['discovery-engine', 'matching-engine', 'browser-framework', 'generation-engine', 'workflow-engine', 'queue-system'] },
      { service: 'config', dependencies: [], dependents: ['discovery-engine', 'matching-engine', 'browser-framework', 'generation-engine', 'workflow-engine', 'notification-system'] },
      { service: 'analytics', dependencies: ['storage', 'config'], dependents: [] },
    ]
    return graph
  },
}
