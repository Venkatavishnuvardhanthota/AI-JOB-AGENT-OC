import type { LogEntry, LogLevel, CorrelationContext, ServiceName } from './production-types'
import { nowISO } from '../orchestration/utils'

const PREFIX = 'ajapp_log_'
const MAX_LOG_ENTRIES = 10000
const SENSITIVE_FIELDS = ['password', 'secret', 'token', 'apiKey', 'api_key', 'authorization', 'ssn', 'credit_card']
const SENSITIVE_PATTERNS = [
  /secret/i, /password/i, /token/i, /api.?key/i, /auth/i, /ssn/i, /credit.?card/i,
  /bearer\s+\S+/gi, /key=\S+/gi,
]

function maskSensitiveData(data: Record<string, unknown>): Record<string, unknown> {
  const masked: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(data)) {
    if (SENSITIVE_FIELDS.some(f => key.toLowerCase().includes(f))) {
      masked[key] = '***MASKED***'
    } else if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      masked[key] = maskSensitiveData(value as Record<string, unknown>)
    } else if (typeof value === 'string' && SENSITIVE_PATTERNS.some(p => p.test(value))) {
      masked[key] = '***MASKED***'
    } else {
      masked[key] = value
    }
  }
  return masked
}

function sanitizeMessage(msg: string): string {
  let sanitized = msg
  for (const pattern of SENSITIVE_PATTERNS) {
    sanitized = sanitized.replace(pattern, '***MASKED***')
  }
  return sanitized
}

function get<T>(key: string, fallback: T): T {
  try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback } catch { return fallback }
}
function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

export const loggingService = {
  debug(message: string, context?: CorrelationContext, data?: Record<string, unknown>, service?: ServiceName): LogEntry {
    return this.log('debug', message, context, data, service)
  },

  info(message: string, context?: CorrelationContext, data?: Record<string, unknown>, service?: ServiceName): LogEntry {
    return this.log('info', message, context, data, service)
  },

  warn(message: string, context?: CorrelationContext, data?: Record<string, unknown>, service?: ServiceName): LogEntry {
    return this.log('warn', message, context, data, service)
  },

  error(message: string, error?: Error | { message: string; code?: string }, context?: CorrelationContext, data?: Record<string, unknown>, service?: ServiceName): LogEntry {
    const errData = error ? { message: error.message, code: (error as any).code, stack: (error as Error).stack } : undefined
    return this.log('error', message, context, { ...data, error: errData }, service)
  },

  fatal(message: string, error?: Error, context?: CorrelationContext, data?: Record<string, unknown>, service?: ServiceName): LogEntry {
    return this.log('fatal', message, context, { ...data, error: error ? { message: error.message, stack: error.stack } : undefined }, service)
  },

  log(level: LogLevel, message: string, context?: CorrelationContext, data?: Record<string, unknown>, service?: ServiceName): LogEntry {
    const entry: LogEntry = {
      timestamp: nowISO(),
      level,
      message: sanitizeMessage(message),
      context: context ?? { correlationId: 'no-correlation' },
      service,
      data: data ? maskSensitiveData(data as Record<string, unknown>) : undefined,
    }

    const entries = this.getAll()
    entries.unshift(entry)
    set(PREFIX + 'entries', entries.slice(0, MAX_LOG_ENTRIES))

    if (level === 'error' || level === 'fatal') {
      console.error(`[${level.toUpperCase()}]`, entry.message, entry)
    } else if (level === 'warn') {
      console.warn(`[${level.toUpperCase()}]`, entry.message, entry)
    } else {
      console.log(`[${level.toUpperCase()}]`, entry.message, entry)
    }

    return entry
  },

  getAll(): LogEntry[] {
    return get<LogEntry[]>(PREFIX + 'entries', [])
  },

  getByLevel(level: LogLevel): LogEntry[] {
    return this.getAll().filter(e => e.level === level)
  },

  getByService(service: ServiceName): LogEntry[] {
    return this.getAll().filter(e => e.service === service)
  },

  getByCorrelationId(correlationId: string): LogEntry[] {
    return this.getAll().filter(e => e.context.correlationId === correlationId)
  },

  getByWorkflowId(workflowId: string): LogEntry[] {
    return this.getAll().filter(e => e.context.workflowId === workflowId)
  },

  search(query: string): LogEntry[] {
    const q = query.toLowerCase()
    return this.getAll().filter(e =>
      e.message.toLowerCase().includes(q) ||
      e.context.correlationId.toLowerCase().includes(q) ||
      e.context.workflowId?.toLowerCase().includes(q)
    )
  },

  getRecent(count: number = 100): LogEntry[] {
    return this.getAll().slice(0, count)
  },

  getErrors(count: number = 50): LogEntry[] {
    return this.getAll().filter(e => e.level === 'error' || e.level === 'fatal').slice(0, count)
  },

  clear(): void {
    set(PREFIX + 'entries', [])
  },

  toJSON(entries?: LogEntry[]): string {
    return JSON.stringify(entries ?? this.getAll(), null, 2)
  },

  exportAsJSON(): string {
    return this.toJSON()
  },
}
