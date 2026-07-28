import type { ActionOptions, DOMElement, ActionType } from './types'
import { DEFAULT_ACTION_OPTIONS } from './types'
import { sleep, randomBetween } from './utils'

const PREFIX = 'ajapp_brw_act_'

function get<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch { return fallback }
}

function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

export const actionEngine = {
  async click(
    element: DOMElement | null,
    sessionId: string,
    options: Partial<ActionOptions> = {}
  ): Promise<boolean> {
    const opts = { ...DEFAULT_ACTION_OPTIONS, ...options }
    return this.executeAction('click', element, sessionId, opts, () => {
      if (!element) throw new Error('Element not found')
      if (!element.enabled) throw new Error('Element is disabled')
      return true
    })
  },

  async doubleClick(
    element: DOMElement | null,
    sessionId: string,
    options: Partial<ActionOptions> = {}
  ): Promise<boolean> {
    const opts = { ...DEFAULT_ACTION_OPTIONS, ...options }
    return this.executeAction('dblclick', element, sessionId, opts, () => {
      if (!element) throw new Error('Element not found')
      return true
    })
  },

  async hover(
    element: DOMElement | null,
    sessionId: string,
    options: Partial<ActionOptions> = {}
  ): Promise<boolean> {
    const opts = { ...DEFAULT_ACTION_OPTIONS, ...options }
    return this.executeAction('hover', element, sessionId, opts, () => {
      if (!element) throw new Error('Element not found')
      return true
    })
  },

  async type(
    element: DOMElement | null,
    _text: string,
    sessionId: string,
    options: Partial<ActionOptions> = {}
  ): Promise<boolean> {
    const opts = { ...DEFAULT_ACTION_OPTIONS, ...options }
    return this.executeAction('type', element, sessionId, opts, () => {
      if (!element) throw new Error('Element not found')
      if (element.readonly) throw new Error('Element is read-only')
      return true
    })
  },

  async select(
    element: DOMElement | null,
    _value: string,
    sessionId: string,
    options: Partial<ActionOptions> = {}
  ): Promise<boolean> {
    const opts = { ...DEFAULT_ACTION_OPTIONS, ...options }
    return this.executeAction('select', element, sessionId, opts, () => {
      if (!element) throw new Error('Element not found')
      return true
    })
  },

  async check(
    element: DOMElement | null,
    sessionId: string,
    options: Partial<ActionOptions> = {}
  ): Promise<boolean> {
    const opts = { ...DEFAULT_ACTION_OPTIONS, ...options }
    return this.executeAction('check', element, sessionId, opts, () => {
      if (!element) throw new Error('Element not found')
      if (element.checked) return false
      return true
    })
  },

  async scroll(
    _x: number,
    _y: number,
    sessionId: string,
    options: Partial<ActionOptions> = {}
  ): Promise<boolean> {
    return this.executeAction('scroll', null, sessionId, { ...DEFAULT_ACTION_OPTIONS, ...options }, () => {
      return true
    })
  },

  async upload(
    element: DOMElement | null,
    _filePath: string,
    sessionId: string,
    options: Partial<ActionOptions> = {}
  ): Promise<boolean> {
    const opts = { ...DEFAULT_ACTION_OPTIONS, ...options }
    return this.executeAction('upload', element, sessionId, opts, () => {
      if (!element) throw new Error('File input not found')
      if (element.type !== 'file') throw new Error('Element is not a file input')
      return true
    })
  },

  async executeAction(
    type: ActionType,
    element: DOMElement | null,
    sessionId: string,
    options: ActionOptions,
    action: () => boolean
  ): Promise<boolean> {
    let lastError: Error | null = null
    for (let attempt = 0; attempt <= options.retries; attempt++) {
      try {
        if (options.delay > 0) await sleep(randomBetween(10, options.delay))
        const result = action()
        this.logAction(sessionId, type, element, true, null)
        return result
      } catch (err) {
        lastError = err instanceof Error ? err : new Error(String(err))
        if (attempt < options.retries) {
          await sleep(500 * Math.pow(2, attempt))
        }
      }
    }
    this.logAction(sessionId, type, element, false, lastError?.message ?? 'Unknown error')
    return false
  },

  logAction(sessionId: string, type: ActionType, element: DOMElement | null, success: boolean, error: string | null): void {
    const history = get<{ type: ActionType; element: string | null; success: boolean; error: string | null; timestamp: string }[]>(`${PREFIX}${sessionId}`, [])
    history.unshift({ type, element: element?.tag ?? null, success, error, timestamp: new Date().toISOString() })
    set(`${PREFIX}${sessionId}`, history.slice(0, 500))
  },

  getHistory(sessionId: string): { type: ActionType; element: string | null; success: boolean; error: string | null; timestamp: string }[] {
    return get(`${PREFIX}${sessionId}`, [])
  },

  clearHistory(sessionId: string): void {
    set(`${PREFIX}${sessionId}`, [])
  },
}
