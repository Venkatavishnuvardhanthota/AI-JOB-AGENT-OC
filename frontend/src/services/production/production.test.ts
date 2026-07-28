import { describe, it, expect, beforeEach } from 'vitest'
import { observabilityService } from './observability-service'
import { loggingService } from './logging-service'
import { metricsService, recordJobDiscovered, recordJobMatched, recordPackageGenerated, recordBrowserSession, recordWorkflowExecution, recordRetry, recordFailure, recordRecovery } from './metrics-service'
import { healthService } from './health-service'
import { alertService, raiseHighErrorRate, raiseWorkflowFailure, raiseBrowserCrash, raiseQueueBacklog, raiseRetryStorm, raiseProviderFailure, raiseSlowResponse } from './alert-service'
import { configService } from './config-service'
import { securityService, secureStorage } from './security-service'
import { performanceService } from './performance-service'
import { recoveryService } from './recovery-analytics-service'
import { maintenanceService } from './maintenance-service'
import { diagnosticsService } from './diagnostics-service'

beforeEach(() => { localStorage.clear() })

describe('observability-service', () => {
  it('generates correlation IDs', () => {
    const id = observabilityService.getCorrelationId()
    expect(id).toMatch(/^corr_/)
  })

  it('sets custom correlation IDs', () => {
    observabilityService.setCorrelationId('custom-id')
    expect(observabilityService.getCorrelationId()).toBe('custom-id')
  })

  it('resets correlation IDs', () => {
    const first = observabilityService.getCorrelationId()
    observabilityService.resetCorrelationId()
    expect(observabilityService.getCorrelationId()).not.toBe(first)
  })

  it('creates context with defaults', () => {
    const ctx = observabilityService.createContext()
    expect(ctx.correlationId).toBeTruthy()
    expect(ctx.requestId).toMatch(/^req_/)
  })

  it('creates context with overrides', () => {
    const ctx = observabilityService.createContext({ workflowId: 'wf_123' })
    expect(ctx.workflowId).toBe('wf_123')
  })

  it('starts and ends spans', () => {
    const span = observabilityService.startSpan('test-op')
    expect(span.spanId).toMatch(/^span_/)
    const duration = observabilityService.endSpan(span)
    expect(duration).toBeGreaterThanOrEqual(0)
  })
})

describe('logging-service', () => {
  it('logs at different levels', () => {
    const debug = loggingService.debug('debug msg')
    const info = loggingService.info('info msg')
    const warn = loggingService.warn('warn msg')
    const err = loggingService.error('err msg')
    expect(debug.level).toBe('debug')
    expect(info.level).toBe('info')
    expect(warn.level).toBe('warn')
    expect(err.level).toBe('error')
  })

  it('filters logs by level', () => {
    loggingService.info('test1')
    loggingService.error('test2')
    expect(loggingService.getByLevel('info')).toHaveLength(1)
    expect(loggingService.getByLevel('error')).toHaveLength(1)
  })

  it('filters logs by service', () => {
    loggingService.info('svc msg', undefined, undefined, 'workflow-engine')
    expect(loggingService.getByService('workflow-engine')).toHaveLength(1)
  })

  it('filters logs by correlation ID', () => {
    const ctx = { correlationId: 'test-corr' }
    loggingService.info('msg', ctx)
    expect(loggingService.getByCorrelationId('test-corr')).toHaveLength(1)
  })

  it('searches logs', () => {
    loggingService.info('unique search term')
    expect(loggingService.search('unique')).toHaveLength(1)
    expect(loggingService.search('nonexistent')).toHaveLength(0)
  })

  it('masks sensitive data in log entries', () => {
    loggingService.info('user action', undefined, { password: 'mysecret123', token: 'abc', safeField: 'hello' })
    const logs = loggingService.getAll()
    expect(logs[0].data?.password).toBe('***MASKED***')
    expect(logs[0].data?.token).toBe('***MASKED***')
    expect(logs[0].data?.safeField).toBe('hello')
  })

  it('exports logs as JSON', () => {
    loggingService.info('export test')
    const json = loggingService.exportAsJSON()
    expect(() => JSON.parse(json)).not.toThrow()
  })

  it('clears all logs', () => {
    loggingService.info('to be cleared')
    loggingService.clear()
    expect(loggingService.getAll()).toHaveLength(0)
  })

  it('gets recent logs', () => {
    loggingService.info('recent1')
    loggingService.info('recent2')
    expect(loggingService.getRecent(1)).toHaveLength(1)
  })
})

describe('metrics-service', () => {
  it('records metrics', () => {
    metricsService.record('test.metric', 42, 'count', {}, 'analytics')
    expect(metricsService.getCurrentValue('test.metric')).toBe(42)
  })

  it('increments metrics', () => {
    metricsService.increment('test.counter')
    expect(metricsService.getCurrentValue('test.counter')).toBe(1)
    metricsService.increment('test.counter')
    expect(metricsService.getCurrentValue('test.counter')).toBe(2)
  })

  it('records duration metrics', () => {
    metricsService.recordDuration('api.call', 150)
    expect(metricsService.getAggregatedValue('api.call', {}, 'avg')).toBeGreaterThan(0)
  })

  it('gets aggregated values', () => {
    metricsService.record('agg.test', 10, 'count')
    metricsService.record('agg.test', 20, 'count')
    metricsService.record('agg.test', 30, 'count')
    expect(metricsService.getAggregatedValue('agg.test', {}, 'avg')).toBe(20)
    expect(metricsService.getAggregatedValue('agg.test', {}, 'sum')).toBe(60)
    expect(metricsService.getAggregatedValue('agg.test', {}, 'min')).toBe(10)
    expect(metricsService.getAggregatedValue('agg.test', {}, 'max')).toBe(30)
  })

  it('lists all metric names', () => {
    metricsService.record('metric.a', 1)
    metricsService.record('metric.b', 2)
    const names = metricsService.getAllMetricNames()
    expect(names).toContain('metric.a')
    expect(names).toContain('metric.b')
  })

  it('convenience recorders work', () => {
    recordJobDiscovered()
    recordJobMatched()
    recordPackageGenerated()
    recordBrowserSession()
    recordWorkflowExecution()
    recordRetry()
    recordFailure()
    recordRecovery()
    expect(metricsService.getCurrentValue('jobs.discovered')).toBe(1)
    expect(metricsService.getCurrentValue('jobs.matched')).toBe(1)
    expect(metricsService.getCurrentValue('packages.generated')).toBe(1)
    expect(metricsService.getCurrentValue('browser.sessions')).toBe(1)
    expect(metricsService.getCurrentValue('workflow.executions')).toBe(1)
    expect(metricsService.getCurrentValue('workflow.retries')).toBe(1)
    expect(metricsService.getCurrentValue('workflow.failures')).toBe(1)
    expect(metricsService.getCurrentValue('workflow.recoveries')).toBe(1)
  })
})

describe('health-service', () => {
  it('checks individual services', () => {
    const health = healthService.check('discovery-engine')
    expect(health.service).toBe('discovery-engine')
    expect(['healthy', 'warning', 'degraded', 'critical']).toContain(health.status)
  })

  it('checks all services', () => {
    const results = healthService.checkAll()
    expect(results.length).toBeGreaterThanOrEqual(5)
  })

  it('gets overall status', () => {
    const overall = healthService.getOverallStatus()
    expect(overall.total).toBeGreaterThanOrEqual(5)
  })

  it('reports errors', () => {
    healthService.reportError('workflow-engine')
    const health = healthService.getStatus('workflow-engine')
    expect(health?.errorCount).toBeGreaterThanOrEqual(1)
  })

  it('clears errors', () => {
    healthService.reportError('discovery-engine')
    healthService.clearErrors('discovery-engine')
    expect(healthService.getStatus('discovery-engine')?.errorCount).toBe(0)
  })

  it('resets all health', () => {
    healthService.reportError('matching-engine')
    healthService.resetAll()
    const health = healthService.getStatus('matching-engine')
    expect(health?.errorCount).toBe(0)
    expect(health?.status).toBe('healthy')
  })
})

describe('alert-service', () => {
  it('raises alerts', () => {
    const alert = alertService.raise('Test Alert', 'Test message', 'warning', 'workflow-engine', 'test')
    expect(alert.title).toBe('Test Alert')
    expect(alert.status).toBe('active')
  })

  it('acknowledges alerts', () => {
    const alert = alertService.raise('Test', 'Msg', 'info', 'analytics', 'test')
    const ack = alertService.acknowledge(alert.id)
    expect(ack?.status).toBe('acknowledged')
  })

  it('resolves alerts', () => {
    const alert = alertService.raise('Test', 'Msg', 'error', 'browser-framework', 'test')
    alertService.resolve(alert.id)
    expect(alertService.getAll()[0].status).toBe('resolved')
  })

  it('suppresses alerts', () => {
    const alert = alertService.raise('Test', 'Msg', 'critical', 'queue-system', 'test')
    alertService.suppress(alert.id)
    expect(alertService.getActive()).toHaveLength(0)
  })

  it('gets alerts by severity', () => {
    alertService.raise('A', 'M1', 'info', 'config', 't')
    alertService.raise('B', 'M2', 'critical', 'storage', 't')
    expect(alertService.getBySeverity('critical')).toHaveLength(1)
    expect(alertService.getBySeverity('info')).toHaveLength(1)
  })

  it('counts alerts', () => {
    alertService.raise('A', 'M', 'warning', 'analytics', 't')
    const counts = alertService.getAlertCounts()
    expect(counts.active).toBe(1)
  })

  it('raises convenience alerts', () => {
    raiseHighErrorRate(15, 10, 'workflow-engine')
    raiseWorkflowFailure('wf_1', 'Engineer', 'Co')
    raiseBrowserCrash('browser_1')
    raiseQueueBacklog(200, 50)
    raiseRetryStorm(50, 5)
    raiseProviderFailure('indeed', 'timeout')
    raiseSlowResponse('submit', 10000, 5000)
    expect(alertService.getAll().length).toBeGreaterThanOrEqual(7)
  })
})

describe('config-service', () => {
  it('returns default config', () => {
    const config = configService.get()
    expect(config.environment).toBe('development')
    expect(config.version).toBe('2.1.0')
  })

  it('updates config', () => {
    configService.update({ environment: 'production' })
    expect(configService.get().environment).toBe('production')
  })

  it('gets and sets feature flags', () => {
    expect(configService.getFeatureFlag('orchestration')).toBe(true)
    configService.setFeatureFlag('orchestration', false)
    expect(configService.getFeatureFlag('orchestration')).toBe(false)
  })

  it('toggles providers', () => {
    expect(configService.isProviderEnabled('indeed')).toBe(true)
    configService.toggleProvider('indeed', false)
    expect(configService.isProviderEnabled('indeed')).toBe(false)
  })

  it('gets thresholds', () => {
    expect(configService.getThreshold('maxRetries')).toBe(3)
  })

  it('resets to defaults', () => {
    configService.update({ environment: 'production' })
    configService.reset()
    expect(configService.get().environment).toBe('development')
  })

  it('validates config', () => {
    const result = configService.validate()
    expect(result.valid).toBe(true)
  })
})

describe('security-service', () => {
  it('masks sensitive strings', () => {
    expect(securityService.maskSensitive('myapikey123')).toBe('my****23')
  })

  it('sanitizes log data', () => {
    const sanitized = securityService.sanitizeForLog({ password: 'secret', name: 'John' })
    expect(sanitized.password).toBe('[REDACTED]')
    expect(sanitized.name).toBe('John')
  })

  it('sanitizes messages', () => {
    const msg = securityService.sanitizeMessage('Bearer mytoken123')
    expect(msg).toContain('[REDACTED]')
  })

  it('validates input', () => {
    expect(securityService.validateInput('  hello  ')).toBe('hello')
    expect(securityService.validateInput('')).toBe('')
  })

  it('sanitizes output', () => {
    expect(securityService.sanitizeOutput('<script>alert("xss")</script>')).not.toContain('<script>')
  })

  it('stores and retrieves secrets', () => {
    securityService.storeSecret('api_key', 'sk-123456')
    expect(securityService.getSecret('api_key')).toBe('sk-123456')
  })

  it('checks permissions', () => {
    expect(securityService.hasPermission('admin', 'user')).toBe(true)
    expect(securityService.hasPermission('user', 'admin')).toBe(false)
  })

  it('rate limits keys', () => {
    const result = securityService.rateLimitKey('test-key', 5, 60000)
    expect(result.allowed).toBe(true)
    expect(result.remaining).toBe(4)
  })
})

describe('performance-service', () => {
  it('records performance samples', () => {
    const sample = performanceService.record('test-op', 100, 'workflow-engine', { job: 'test' }, true)
    expect(sample.operation).toBe('test-op')
    expect(sample.duration).toBe(100)
    expect(sample.success).toBe(true)
  })

  it('gets recent operations', () => {
    performanceService.record('op1', 50)
    performanceService.record('op2', 150)
    expect(performanceService.getRecentOperations(10)).toHaveLength(2)
  })

  it('computes average duration', () => {
    performanceService.record('avg-op', 100)
    performanceService.record('avg-op', 200)
    expect(performanceService.getAverageDuration('avg-op')).toBe(150)
  })

  it('gets slowest operations', () => {
    performanceService.record('slow-op', 9000, 'workflow-engine', {}, true)
    performanceService.record('fast-op', 10, 'workflow-engine', {}, true)
    const slowest = performanceService.getSlowestOperations(1)
    expect(slowest[0].operation).toBe('slow-op')
  })
})

describe('recovery-service', () => {
  it('records recovery attempts', () => {
    recoveryService.record('wf_1', 'navigating', true)
    expect(recoveryService.getHistory('wf_1')).toHaveLength(1)
  })

  it('provides recovery analytics', () => {
    recoveryService.record('wf_1', 'filling', true)
    recoveryService.record('wf_2', 'submitting', false)
    const analytics = recoveryService.getAnalytics()
    expect(analytics.totalRecoveries).toBe(2)
    expect(analytics.successRate).toBe(50)
  })

  it('clears history', () => {
    recoveryService.record('wf_1', 'test', true)
    recoveryService.clearHistory('wf_1')
    expect(recoveryService.getHistory('wf_1')).toHaveLength(0)
  })
})

describe('maintenance-service', () => {
  it('returns default tasks', () => {
    const tasks = maintenanceService.getTasks()
    expect(tasks.length).toBeGreaterThan(0)
  })

  it('toggles tasks', () => {
    const tasks = maintenanceService.getTasks()
    const task = maintenanceService.toggleTask(tasks[0].id)
    expect(task?.enabled).toBe(false)
  })

  it('runs log pruning task', () => {
    loggingService.info('old log entry')
    loggingService.info('another log')
    const tasks = maintenanceService.getTasks()
    const logTask = tasks.find(t => t.target === 'logs')
    if (logTask) {
      const result = maintenanceService.runTask(logTask.id)
      expect(result.success).toBe(true)
    }
  })

  it('runs all enabled tasks', () => {
    const result = maintenanceService.runAll()
    expect(result.success).toBeGreaterThanOrEqual(0)
  })
})

describe('diagnostics-service', () => {
  it('generates diagnostic reports', () => {
    const report = diagnosticsService.generateReport()
    expect(report.system.version).toBe('2.1.0')
    expect(report.services.length).toBeGreaterThanOrEqual(5)
    expect(report.recommendations.length).toBeGreaterThan(0)
  })

  it('provides dependency graph', () => {
    const graph = diagnosticsService.getServiceDependencyGraph()
    expect(graph.length).toBeGreaterThan(0)
    expect(graph[0].dependencies).toBeDefined()
    expect(graph[0].dependents).toBeDefined()
  })
})
