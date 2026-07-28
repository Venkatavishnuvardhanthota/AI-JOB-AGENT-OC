import type { BrowserMonitoringReport } from './types'
import { browserFactory } from './browser-factory'
import { navigationEngine } from './navigation-engine'
import { loggingService } from './logging-service'

export const monitoringService = {
  generateReport(browserId: string): BrowserMonitoringReport {
    const browser = browserFactory.get(browserId)
    if (!browser) throw new Error(`Browser ${browserId} not found`)

    const sessions = browser.sessions
    const activeSessions = sessions.filter(s => s.status === 'active')
    const recentLogs = loggingService.getRecent(browserId, 50)
    const warnings = recentLogs
      .filter(l => l.level === 'warn' || l.level === 'error')
      .map(l => `[${l.level.toUpperCase()}] ${l.source}: ${l.message}`)

    return {
      browserId,
      sessions: sessions.length,
      activeSessions: activeSessions.length,
      totalNavigations: browser.metrics.pageLoads,
      totalActions: browser.metrics.actions,
      totalErrors: browser.metrics.errors,
      successRate: this.calculateSuccessRate(browserId),
      averageNavigationTime: this.calculateAvgNavTime(browserId),
      memoryUsage: browser.metrics.memoryUsage,
      uptime: browser.metrics.uptime,
      recentLogs,
      warnings,
    }
  },

  getAllReports(): BrowserMonitoringReport[] {
    return browserFactory.listAll().map(b => this.generateReport(b.id))
  },

  calculateSuccessRate(browserId: string): number {
    const browser = browserFactory.get(browserId)
    if (!browser || browser.metrics.pageLoads === 0) return 100
    const errorRate = browser.metrics.errors / browser.metrics.pageLoads
    return Math.round((1 - errorRate) * 100)
  },

  calculateAvgNavTime(browserId: string): number {
    let totalTime = 0
    let count = 0
    for (const session of browserFactory.get(browserId)?.sessions ?? []) {
      const history = navigationEngine.getHistory(session.id)
      for (const nav of history) {
        totalTime += nav.duration
        count++
      }
    }
    return count > 0 ? Math.round(totalTime / count) : 0
  },

  getOverallHealth(): { ok: boolean; activeBrowsers: number; totalErrors: number; warnings: string[] } {
    const reports = this.getAllReports()
    const totalErrors = reports.reduce((s, r) => s + r.totalErrors, 0)
    const warnings = reports.flatMap(r => r.warnings)
    return {
      ok: totalErrors < 10,
      activeBrowsers: browserFactory.getActiveCount(),
      totalErrors,
      warnings,
    }
  },
}
