import type { BrowserConfig, BrowserProvider, BrowserState, BrowserMetrics, BrowserSessionSummary } from './types'
import { v4Service } from './utils'

const PREFIX = 'ajapp_brw_'

function get<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(PREFIX + key)
    return raw ? JSON.parse(raw) : fallback
  } catch { return fallback }
}

function set<T>(key: string, value: T): void {
  try { localStorage.setItem(PREFIX + key, JSON.stringify(value)) } catch {}
}

export const browserFactory = {
  create(provider: BrowserProvider, config: BrowserConfig): BrowserState {
    const id = v4Service.generate('brw')
    const now = new Date().toISOString()
    const browser: BrowserState = {
      id,
      provider,
      status: 'idle',
      createdAt: now,
      lastUsedAt: null,
      sessions: [],
      metrics: { uptime: 0, pageLoads: 0, actions: 0, errors: 0, memoryUsage: null, cpuUsage: null },
    }
    const browsers = this.listAll()
    browsers.push(browser)
    set('browsers', browsers)
    set(`config_${id}`, config)
    return browser
  },

  listAll(): BrowserState[] {
    return get<BrowserState[]>('browsers', [])
  },

  get(id: string): BrowserState | undefined {
    return this.listAll().find(b => b.id === id)
  },

  getConfig(id: string): BrowserConfig | undefined {
    return get<BrowserConfig | undefined>(`config_${id}`, undefined)
  },

  update(id: string, updates: Partial<BrowserState>): void {
    const browsers = this.listAll()
    const idx = browsers.findIndex(b => b.id === id)
    if (idx !== -1) {
      browsers[idx] = { ...browsers[idx], ...updates }
      set('browsers', browsers)
    }
  },

  remove(id: string): void {
    const browsers = this.listAll().filter(b => b.id !== id)
    set('browsers', browsers)
    localStorage.removeItem(PREFIX + `config_${id}`)
    localStorage.removeItem(PREFIX + `sessions_${id}`)
  },

  updateMetrics(id: string, metrics: Partial<BrowserMetrics>): void {
    const browser = this.get(id)
    if (browser) {
      this.update(id, { metrics: { ...browser.metrics, ...metrics } })
    }
  },

  addSession(browserId: string, summary: BrowserSessionSummary): void {
    const browser = this.get(browserId)
    if (browser) {
      this.update(browserId, { sessions: [...browser.sessions, summary] })
    }
  },

  getActiveCount(): number {
    return this.listAll().filter(b => b.status === 'running').length
  },

  getTotalCount(): number {
    return this.listAll().length
  },
}
