import type { AuthSessionRecord, AuthConfiguration } from './types'
import { DEFAULT_AUTH_CONFIGURATION } from './types'
import { v4Service, nowISO } from '../orchestration/utils'

const PREFIX = 'ajapp_auth_sess_'

function get<T>(key: string, fallback: T): T {
  try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback } catch { return fallback }
}
function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

function sessionKey(providerId: string, sessionId: string): string {
  return `${PREFIX}${providerId}_${sessionId}`
}

function providerKey(providerId: string): string {
  return `${PREFIX}list_${providerId}`
}

export const authSessionManager = {
  create(providerId: string, strategyId: string, method: AuthSessionRecord['method'], sessionData: Record<string, unknown>, expiresAt: string | null, config?: Partial<AuthConfiguration>): AuthSessionRecord {
    const cfg = { ...DEFAULT_AUTH_CONFIGURATION, ...config }
    const existing = this.listByProvider(providerId)
    if (existing.length >= cfg.maxConcurrentSessions) {
      const oldest = existing.sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime())[0]
      this.destroy(providerId, oldest.id)
    }

    const record: AuthSessionRecord = {
      id: `sess_${v4Service.generate('').slice(0, 16)}`,
      providerId,
      strategyId,
      method,
      authenticated: true,
      createdAt: nowISO(),
      expiresAt,
      lastUsedAt: nowISO(),
      sessionData,
      metadata: {},
    }
    set(sessionKey(providerId, record.id), record)
    this.updateProviderList(providerId, record.id)
    return record
  },

  get(providerId: string, sessionId: string): AuthSessionRecord | null {
    return get<AuthSessionRecord | null>(sessionKey(providerId, sessionId), null)
  },

  update(providerId: string, sessionId: string, updates: Partial<AuthSessionRecord>): void {
    const record = this.get(providerId, sessionId)
    if (record) {
      const updated = { ...record, ...updates, lastUsedAt: nowISO() }
      set(sessionKey(providerId, sessionId), updated)
    }
  },

  destroy(providerId: string, sessionId: string): void {
    localStorage.removeItem(sessionKey(providerId, sessionId))
    this.removeFromProviderList(providerId, sessionId)
  },

  listByProvider(providerId: string): AuthSessionRecord[] {
    const ids = get<string[]>(providerKey(providerId), [])
    return ids.map(id => this.get(providerId, id)).filter((s): s is AuthSessionRecord => s !== null)
  },

  listAll(): AuthSessionRecord[] {
    const keys = Object.keys(localStorage).filter(k => k.startsWith(PREFIX) && k.includes('_sess_') && !k.includes('_list_'))
    return keys.map(k => {
      try { return JSON.parse(localStorage.getItem(k)!) as AuthSessionRecord } catch { return null }
    }).filter((s): s is AuthSessionRecord => s !== null)
  },

  getActive(): AuthSessionRecord[] {
    return this.listAll().filter(s => s.authenticated && (!s.expiresAt || new Date(s.expiresAt).getTime() > Date.now()))
  },

  getExpired(): AuthSessionRecord[] {
    return this.listAll().filter(s => s.expiresAt && new Date(s.expiresAt).getTime() <= Date.now())
  },

  cleanupExpired(): number {
    const expired = this.getExpired()
    for (const s of expired) {
      this.destroy(s.providerId, s.id)
    }
    return expired.length
  },

  touch(providerId: string, sessionId: string): void {
    this.update(providerId, sessionId, { lastUsedAt: nowISO() })
  },

  exists(providerId: string): boolean {
    const ids = get<string[]>(providerKey(providerId), [])
    return ids.length > 0
  },

  getCount(providerId?: string): number {
    if (providerId) return this.listByProvider(providerId).length
    return this.listAll().length
  },

  updateProviderList(providerId: string, sessionId: string): void {
    const ids = get<string[]>(providerKey(providerId), [])
    if (!ids.includes(sessionId)) ids.push(sessionId)
    set(providerKey(providerId), ids)
  },

  removeFromProviderList(providerId: string, sessionId: string): void {
    const ids = get<string[]>(providerKey(providerId), [])
    set(providerKey(providerId), ids.filter(id => id !== sessionId))
  },
}
