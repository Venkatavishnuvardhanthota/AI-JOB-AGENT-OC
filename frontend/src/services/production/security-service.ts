const SENSITIVE_FIELDS = ['password', 'secret', 'token', 'apiKey', 'api_key', 'authorization', 'ssn', 'credit_card', 'jwt']
const SENSITIVE_PATTERNS = [
  /bearer\s+\S+/gi,
  /key=\S+/gi,
  /api[-_]?key['":]\s*['"][^'"]+['"]/gi,
  /password['":]\s*['"][^'"]+['"]/gi,
  /secret['":]\s*['"][^'"]+['"]/gi,
  /token['":]\s*['"][^'"]+['"]/gi,
  /authorization['":]\s*['"][^'"]+['"]/gi,
]

export interface SecureStorage {
  get(key: string): string | null
  set(key: string, value: string): void
  remove(key: string): void
  clear(): void
}

const PREFIX = 'ajapp_sec_'

export const secureStorage: SecureStorage = {
  get(key: string): string | null {
    try {
      const raw = localStorage.getItem(PREFIX + key)
      return raw ? atob(raw) : null
    } catch { return null }
  },

  set(key: string, value: string): void {
    try {
      localStorage.setItem(PREFIX + key, btoa(value))
    } catch { /* silently fail */ }
  },

  remove(key: string): void {
    localStorage.removeItem(PREFIX + key)
  },

  clear(): void {
    const keys = Object.keys(localStorage).filter(k => k.startsWith(PREFIX))
    for (const key of keys) localStorage.removeItem(key)
  },
}

export const securityService = {
  maskSensitive(value: string): string {
    if (value.length <= 4) return '****'
    return value.substring(0, 2) + '****' + value.substring(value.length - 2)
  },

  sanitizeForLog(data: Record<string, unknown>): Record<string, unknown> {
    const sanitized: Record<string, unknown> = {}
    for (const [key, value] of Object.entries(data)) {
      if (SENSITIVE_FIELDS.some(f => key.toLowerCase().includes(f))) {
        sanitized[key] = '[REDACTED]'
      } else if (typeof value === 'object' && value !== null) {
        sanitized[key] = this.sanitizeForLog(value as Record<string, unknown>)
      } else {
        sanitized[key] = value
      }
    }
    return sanitized
  },

  sanitizeMessage(message: string): string {
    let sanitized = message
    for (const pattern of SENSITIVE_PATTERNS) {
      sanitized = sanitized.replace(pattern, '[REDACTED]')
    }
    return sanitized
  },

  validateInput(input: string, maxLength: number = 10000): string {
    if (typeof input !== 'string') return ''
    return input.trim().slice(0, maxLength)
  },

  sanitizeOutput(value: string): string {
    return value
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;')
      .replace(/\//g, '&#x2F;')
  },

  storeSecret(key: string, value: string): void {
    secureStorage.set(key, value)
  },

  getSecret(key: string): string | null {
    return secureStorage.get(key)
  },

  removeSecret(key: string): void {
    secureStorage.remove(key)
  },

  hasPermission(userRole: string, requiredRole: string): boolean {
    const roles = ['admin', 'manager', 'user', 'viewer']
    const userIdx = roles.indexOf(userRole)
    const requiredIdx = roles.indexOf(requiredRole)
    if (userIdx === -1 || requiredIdx === -1) return false
    return userIdx <= requiredIdx
  },

  safeErrorMessage(error: Error | string): string {
    const message = typeof error === 'string' ? error : error.message
    if (SENSITIVE_PATTERNS.some(p => p.test(message))) {
      return 'An error occurred. Please try again.'
    }
    return this.sanitizeMessage(message)
  },

  rateLimitKey(key: string, maxRequests: number, windowMs: number): { allowed: boolean; remaining: number; resetAt: string } {
    const now = Date.now()
    const storageKey = `ajapp_rl_${key}`
    try {
      const raw = localStorage.getItem(storageKey)
      const data: { requests: number[] } = raw ? JSON.parse(raw) : { requests: [] }
      const windowStart = now - windowMs
      const recent = data.requests.filter(t => t > windowStart)
      const allowed = recent.length < maxRequests
      if (allowed) {
        recent.push(now)
        localStorage.setItem(storageKey, JSON.stringify({ requests: recent }))
      }
      return { allowed, remaining: Math.max(0, maxRequests - recent.length), resetAt: new Date(now + windowMs).toISOString() }
    } catch {
      return { allowed: true, remaining: maxRequests, resetAt: new Date(now + windowMs).toISOString() }
    }
  },
}
