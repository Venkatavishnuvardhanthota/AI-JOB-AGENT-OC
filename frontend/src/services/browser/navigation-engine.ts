import type { NavigationResult, NavigationOptions, NavigationStatus } from './types'
import { DEFAULT_NAV_OPTIONS } from './types'
import { sleep } from './utils'

const PREFIX = 'ajapp_brw_nav_'

function get<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch { return fallback }
}

function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

export const navigationEngine = {
  async navigate(
    url: string,
    sessionId: string,
    options: Partial<NavigationOptions> = {}
  ): Promise<NavigationResult> {
    const opts = { ...DEFAULT_NAV_OPTIONS, ...options }
    const start = Date.now()
    let lastError: string | null = null
    let finalUrl = url
    let statusCode: number | null = null
    const redirects: string[] = []
    let status: NavigationStatus = 'success'
    let attempt = 0

    while (attempt <= opts.retries) {
      attempt++
      try {
        if (!isValidUrl(url)) throw new Error(`Invalid URL: ${url}`)
        await sleep(opts.retryDelay * attempt)
        const simulatedStatusCode = simulateNavigation(url)
        statusCode = simulatedStatusCode
        if (opts.followRedirects && isRedirect(simulatedStatusCode)) {
          const redirectUrl = simulateRedirect(url)
          redirects.push(url)
          finalUrl = redirectUrl
        }
        if (simulatedStatusCode >= 400) {
          throw new Error(`HTTP ${simulatedStatusCode}`)
        }
        lastError = null
        break
      } catch (err) {
        lastError = err instanceof Error ? err.message : 'Navigation failed'
        status = attempt > opts.retries ? 'error' : 'timeout'
        if (attempt <= opts.retries) {
          await sleep(opts.retryDelay * Math.pow(2, attempt - 1))
        }
      }
    }

    const duration = Date.now() - start
    const result: NavigationResult = {
      url,
      finalUrl,
      status: lastError ? (attempt > opts.retries ? 'error' : 'timeout') : status,
      statusCode,
      duration,
      redirects,
      error: lastError,
      timestamp: new Date().toISOString(),
    }

    this.logNavigation(sessionId, result)
    return result
  },

  async navigateWithRetry(
    url: string,
    sessionId: string,
    options: Partial<NavigationOptions> = {}
  ): Promise<NavigationResult> {
    return this.navigate(url, sessionId, { ...options, retries: (options.retries ?? 3) + 2 })
  },

  async waitForPageReady(timeout: number = 10000): Promise<boolean> {
    await sleep(Math.min(timeout, 2000))
    return true
  },

  isValidUrl(url: string): boolean {
    return isValidUrl(url)
  },

  logNavigation(sessionId: string, result: NavigationResult): void {
    const history = get<NavigationResult[]>(`${PREFIX}${sessionId}`, [])
    history.unshift(result)
    set(`${PREFIX}${sessionId}`, history.slice(0, 200))
  },

  getHistory(sessionId: string): NavigationResult[] {
    return get<NavigationResult[]>(`${PREFIX}${sessionId}`, [])
  },

  clearHistory(sessionId: string): void {
    set(`${PREFIX}${sessionId}`, [])
  },

  getLatest(sessionId: string): NavigationResult | null {
    const history = this.getHistory(sessionId)
    return history.length > 0 ? history[0] : null
  },
}

function isValidUrl(url: string): boolean {
  try {
    new URL(url)
    return true
  } catch { return false }
}

function isRedirect(code: number): boolean {
  return code >= 300 && code < 400
}

function simulateNavigation(_url: string): number {
  const random = Math.random()
  if (random < 0.85) return 200
  if (random < 0.90) return 301
  if (random < 0.93) return 302
  if (random < 0.95) return 403
  if (random < 0.97) return 404
  if (random < 0.99) return 500
  return 503
}

function simulateRedirect(url: string): string {
  try {
    const u = new URL(url)
    if (u.pathname === '/') return `${u.origin}/home`
    return `${u.origin}/redirected`
  } catch { return url }
}
