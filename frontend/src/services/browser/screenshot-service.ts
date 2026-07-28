import type { ScreenshotResult, ScreenshotOptions } from './types'
import { v4Service } from './utils'

const PREFIX = 'ajapp_brw_ss_'

function get<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch { return fallback }
}

function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

export const screenshotService = {
  async capture(
    sessionId: string,
    url: string,
    options: Partial<ScreenshotOptions> = {}
  ): Promise<ScreenshotResult> {
    const opts: ScreenshotOptions = {
      fullPage: options.fullPage ?? true,
      type: options.type ?? 'png',
      quality: options.quality ?? null,
      selector: options.selector ?? null,
      clip: options.clip ?? null,
    }

    const id = v4Service.generate('ss')
    const result: ScreenshotResult = {
      id,
      url,
      filename: `screenshot_${id}.${opts.type}`,
      path: `/screenshots/${sessionId}/${id}.${opts.type}`,
      width: opts.clip?.width ?? 1920,
      height: opts.clip?.height ?? 1080,
      type: opts.selector ? 'element' : opts.fullPage ? 'full_page' : 'region',
      createdAt: new Date().toISOString(),
      metadata: { sessionId, ...opts },
    }

    const screenshots = get<ScreenshotResult[]>(`${PREFIX}${sessionId}`, [])
    screenshots.unshift(result)
    set(`${PREFIX}${sessionId}`, screenshots.slice(0, 100))

    return result
  },

  captureElement(
    sessionId: string,
    url: string,
    selector: string
  ): Promise<ScreenshotResult> {
    return this.capture(sessionId, url, { selector, fullPage: false })
  },

  captureRegion(
    sessionId: string,
    url: string,
    clip: { x: number; y: number; width: number; height: number }
  ): Promise<ScreenshotResult> {
    return this.capture(sessionId, url, { fullPage: false, clip })
  },

  getHistory(sessionId: string): ScreenshotResult[] {
    return get<ScreenshotResult[]>(`${PREFIX}${sessionId}`, [])
  },

  getById(sessionId: string, screenshotId: string): ScreenshotResult | undefined {
    return this.getHistory(sessionId).find(s => s.id === screenshotId)
  },

  delete(sessionId: string, screenshotId: string): void {
    const screenshots = this.getHistory(sessionId).filter(s => s.id !== screenshotId)
    set(`${PREFIX}${sessionId}`, screenshots)
  },

  clearAll(sessionId: string): void {
    set(`${PREFIX}${sessionId}`, [])
  },
}
