export type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'fatal'
export type HealthStatus = 'healthy' | 'warning' | 'degraded' | 'critical' | 'offline'
export type AlertSeverity = 'info' | 'warning' | 'error' | 'critical'
export type AlertStatus = 'active' | 'acknowledged' | 'resolved' | 'suppressed'
export type ServiceName =
  | 'discovery-engine' | 'matching-engine' | 'browser-framework'
  | 'generation-engine' | 'workflow-engine' | 'notification-system'
  | 'queue-system' | 'storage' | 'config' | 'analytics'

export interface CorrelationContext {
  correlationId: string
  requestId?: string
  sessionId?: string
  workflowId?: string
  browserId?: string
  providerId?: string
  userId?: string
}

export interface LogEntry {
  timestamp: string
  level: LogLevel
  message: string
  context: CorrelationContext
  service?: ServiceName
  data?: Record<string, unknown>
  error?: { message: string; stack?: string; code?: string }
  masked?: boolean
}

export interface MetricSample {
  name: string
  value: number
  unit: 'count' | 'ms' | 'percent' | 'bytes' | 'rate'
  timestamp: string
  tags: Record<string, string>
  service: ServiceName
}

export interface MetricSeries {
  name: string
  unit: MetricSample['unit']
  samples: { timestamp: string; value: number }[]
  tags: Record<string, string>
  service: ServiceName
}

export interface ServiceHealth {
  service: ServiceName
  status: HealthStatus
  lastCheck: string
  responseTime: number
  uptime: number
  errorCount: number
  message: string
  details?: Record<string, unknown>
}

export interface Alert {
  id: string
  title: string
  message: string
  severity: AlertSeverity
  status: AlertStatus
  service: ServiceName
  source: string
  timestamp: string
  acknowledgedAt?: string
  resolvedAt?: string
  metadata?: Record<string, unknown>
}

export interface ConfigOption {
  key: string
  value: unknown
  type: 'string' | 'number' | 'boolean' | 'json'
  description: string
  environment: 'all' | 'development' | 'staging' | 'production'
  runtime: boolean
  category: string
}

export interface FeatureFlag {
  key: string
  enabled: boolean
  description: string
  owner: string
  created: string
}

export interface PerformanceSample {
  operation: string
  duration: number
  timestamp: string
  service: ServiceName
  tags: Record<string, string>
  memoryDelta?: number
  success: boolean
}

export interface DiagnosticReport {
  generated: string
  system: {
    version: string
    uptime: number
    totalServices: number
    healthyServices: number
    degradedServices: number
    offlineServices: number
  }
  services: ServiceHealth[]
  metrics: { name: string; current: number; unit: string }[]
  alerts: Alert[]
  config: { key: string; value: unknown }[]
  dependencies: { name: string; status: HealthStatus; version: string }[]
  recommendations: string[]
}

export interface RecoveryRecord {
  workflowId: string
  stage: string
  attempts: number
  lastAttempt: string
  success: boolean
  error?: string
}

export interface MaintenanceTask {
  id: string
  name: string
  type: 'cleanup' | 'prune' | 'rotate' | 'archive' | 'compress'
  target: string
  lastRun: string | null
  nextRun: string | null
  interval: number
  enabled: boolean
  retentionDays: number
}
