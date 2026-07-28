import type { LogEntry, LogLevel } from './types'
import { v4Service } from './utils'
import { browserFactory } from './browser-factory'

const PREFIX = 'ajapp_brw_log_'

function get<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch { return fallback }
}

function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

export const loggingService = {
  log(
    sessionId: string,
    level: LogLevel,
    source: string,
    message: string,
    data: Record<string, unknown> | null = null,
    duration: number | null = null
  ): LogEntry {
    const entry: LogEntry = {
      id: v4Service.generate('log'),
      sessionId,
      level,
      source,
      message,
      data,
      duration,
      timestamp: new Date().toISOString(),
    }

    const logs = get<LogEntry[]>(`${PREFIX}${sessionId}`, [])
    logs.unshift(entry)
    set(`${PREFIX}${sessionId}`, logs.slice(0, 1000))

    const browserId = this.findBrowserId(sessionId)
    if (browserId && level === 'error') {
      const browser = browserFactory.get(browserId)
      if (browser) {
        browserFactory.updateMetrics(browserId, { errors: browser.metrics.errors + 1 })
      }
    }

    return entry
  },

  debug(sessionId: string, source: string, message: string, data?: Record<string, unknown>): LogEntry {
    return this.log(sessionId, 'debug', source, message, data ?? null)
  },

  info(sessionId: string, source: string, message: string, data?: Record<string, unknown>): LogEntry {
    return this.log(sessionId, 'info', source, message, data ?? null)
  },

  warn(sessionId: string, source: string, message: string, data?: Record<string, unknown>): LogEntry {
    return this.log(sessionId, 'warn', source, message, data ?? null)
  },

  error(sessionId: string, source: string, message: string, data?: Record<string, unknown>): LogEntry {
    return this.log(sessionId, 'error', source, message, data ?? null)
  },

  getRecent(sessionId: string, count: number = 100): LogEntry[] {
    return get<LogEntry[]>(`${PREFIX}${sessionId}`, []).slice(0, count)
  },

  getByLevel(sessionId: string, level: LogLevel): LogEntry[] {
    return this.getRecent(sessionId, 1000).filter(l => l.level === level)
  },

  getErrors(sessionId: string): LogEntry[] {
    return this.getByLevel(sessionId, 'error')
  },

  getWarnings(sessionId: string): LogEntry[] {
    return this.getByLevel(sessionId, 'warn')
  },

  clear(sessionId: string): void {
    set(`${PREFIX}${sessionId}`, [])
  },

  clearAll(): void {
    for (const browser of browserFactory.listAll()) {
      for (const session of browser.sessions) {
        this.clear(session.id)
      }
    }
  },

  findBrowserId(sessionId: string): string | null {
    for (const browser of browserFactory.listAll()) {
      if (browser.sessions.some(s => s.id === sessionId)) return browser.id
    }
    return null
  },
}
