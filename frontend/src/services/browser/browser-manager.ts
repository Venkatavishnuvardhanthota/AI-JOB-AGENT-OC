import type { BrowserProvider, BrowserConfig, BrowserState } from './types'
import { DEFAULT_BROWSER_CONFIG } from './types'
import { browserFactory } from './browser-factory'
import { sessionManager } from './session-manager'
import { sleep } from './utils'

export const browserManager = {
  async launch(
    provider: BrowserProvider = 'chromium',
    config: Partial<BrowserConfig> = {}
  ): Promise<BrowserState> {
    const mergedConfig: BrowserConfig = { ...DEFAULT_BROWSER_CONFIG, ...config, provider }
    const browser = browserFactory.create(provider, mergedConfig)
    browser.status = 'running'
    browserFactory.update(browser.id, { status: 'running', lastUsedAt: new Date().toISOString() })

    await sleep(500)
    return browser
  },

  async close(browserId: string): Promise<void> {
    const browser = browserFactory.get(browserId)
    if (!browser) throw new Error(`Browser ${browserId} not found`)

    for (const session of browser.sessions) {
      if (session.status === 'active') {
        sessionManager.close(browserId, session.id)
      }
    }

    browserFactory.update(browserId, { status: 'closed', lastUsedAt: new Date().toISOString() })
    await sleep(200)
  },

  getStatus(browserId: string): BrowserState | undefined {
    return browserFactory.get(browserId)
  },

  listAll(): BrowserState[] {
    return browserFactory.listAll()
  },

  getActiveBrowsers(): BrowserState[] {
    return browserFactory.listAll().filter(b => b.status === 'running')
  },

  getConfig(browserId: string): BrowserConfig | undefined {
    return browserFactory.getConfig(browserId)
  },

  updateConfig(browserId: string, config: Partial<BrowserConfig>): void {
    const existing = browserFactory.getConfig(browserId)
    if (existing) {
      const { provider, ...rest } = config
      const merged: BrowserConfig = { ...existing, ...rest }
      localStorage.setItem('ajapp_brw_config_' + browserId, JSON.stringify(merged))
    }
  },

  createSession(browserId: string, url?: string): ReturnType<typeof sessionManager.create> {
    return sessionManager.create(browserId, url ?? null)
  },

  closeSession(browserId: string, sessionId: string): void {
    sessionManager.close(browserId, sessionId)
  },

  cleanup(): void {
    sessionManager.cleanupExpired()
    const browsers = browserFactory.listAll()
    for (const browser of browsers) {
      const hasActiveSessions = browser.sessions.some(s => s.status === 'active')
      if (!hasActiveSessions && browser.status === 'running') {
        browserFactory.update(browser.id, { status: 'idle' })
      }
    }
  },
}
