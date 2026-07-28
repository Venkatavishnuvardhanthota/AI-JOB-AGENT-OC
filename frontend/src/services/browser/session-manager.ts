import type { BrowserSession, TabInfo } from './types'
import { v4Service } from './utils'
import { browserFactory } from './browser-factory'

const PREFIX = 'ajapp_brw_sess_'

function get<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch { return fallback }
}

function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

export const sessionManager = {
  create(browserId: string, url: string | null = null): BrowserSession {
    const id = v4Service.generate('sess')
    const now = new Date().toISOString()
    const session: BrowserSession = {
      id,
      browserId,
      status: 'active',
      url,
      tabs: [],
      cookies: [],
      storageState: null,
      createdAt: now,
      expiresAt: null,
      lastActivityAt: now,
      metadata: {},
    }
    const sessions = this.listByBrowser(browserId)
    sessions.push(session)
    set(`${PREFIX}${browserId}`, sessions)

    browserFactory.addSession(browserId, {
      id: session.id, status: 'active', url, tabs: 0, createdAt: now, lastActivityAt: now,
    })

    return session
  },

  listByBrowser(browserId: string): BrowserSession[] {
    return get<BrowserSession[]>(`${PREFIX}${browserId}`, [])
  },

  get(browserId: string, sessionId: string): BrowserSession | undefined {
    return this.listByBrowser(browserId).find(s => s.id === sessionId)
  },

  update(browserId: string, sessionId: string, updates: Partial<BrowserSession>): void {
    const sessions = this.listByBrowser(browserId)
    const idx = sessions.findIndex(s => s.id === sessionId)
    if (idx !== -1) {
      sessions[idx] = { ...sessions[idx], ...updates, lastActivityAt: new Date().toISOString() }
      set(`${PREFIX}${browserId}`, sessions)
    }
  },

  close(browserId: string, sessionId: string): void {
    this.update(browserId, sessionId, { status: 'closed' })
  },

  pause(browserId: string, sessionId: string): void {
    this.update(browserId, sessionId, { status: 'paused' })
  },

  resume(browserId: string, sessionId: string): void {
    this.update(browserId, sessionId, { status: 'active' })
  },

  addTab(browserId: string, sessionId: string, tab: TabInfo): void {
    const session = this.get(browserId, sessionId)
    if (session) {
      this.update(browserId, sessionId, { tabs: [...session.tabs, tab], url: tab.url })
    }
  },

  updateTab(browserId: string, sessionId: string, tabId: string, updates: Partial<TabInfo>): void {
    const session = this.get(browserId, sessionId)
    if (session) {
      const tabs = session.tabs.map(t => t.id === tabId ? { ...t, ...updates } : t)
      this.update(browserId, sessionId, { tabs })
    }
  },

  closeTab(browserId: string, sessionId: string, tabId: string): void {
    const session = this.get(browserId, sessionId)
    if (session) {
      this.update(browserId, sessionId, { tabs: session.tabs.filter(t => t.id !== tabId) })
    }
  },

  saveCookies(browserId: string, sessionId: string, cookies: Record<string, unknown>[]): void {
    this.update(browserId, sessionId, { cookies })
  },

  saveStorageState(browserId: string, sessionId: string, state: Record<string, unknown>): void {
    this.update(browserId, sessionId, { storageState: state })
  },

  getActiveSessions(): { browserId: string; session: BrowserSession }[] {
    const result: { browserId: string; session: BrowserSession }[] = []
    for (const browser of browserFactory.listAll()) {
      for (const session of this.listByBrowser(browser.id)) {
        if (session.status === 'active') {
          result.push({ browserId: browser.id, session })
        }
      }
    }
    return result
  },

  cleanupExpired(): number {
    let count = 0
    for (const browser of browserFactory.listAll()) {
      const sessions = this.listByBrowser(browser.id)
      for (const session of sessions) {
        if (session.expiresAt && new Date(session.expiresAt).getTime() < Date.now()) {
          this.update(browser.id, session.id, { status: 'expired' })
          count++
        }
      }
    }
    return count
  },
}
