import { describe, it, expect, beforeEach } from 'vitest'
import { browserFactory } from './browser-factory'
import { sessionManager } from './session-manager'
import { navigationEngine } from './navigation-engine'
import { domInspectionService } from './dom-inspection'
import { actionEngine } from './action-engine'
import { locatorEngine } from './locator-engine'
import { humanBehaviourService } from './human-behaviour'
import { errorRecoveryService } from './error-recovery'
import { monitoringService } from './monitoring-service'
import { screenshotService } from './screenshot-service'
import { downloadService } from './download-service'
import { loggingService } from './logging-service'
import type { DOMElement, BrowserConfig } from './types'

beforeEach(() => {
  localStorage.clear()
})

describe('browserFactory', () => {
  it('creates a browser with default state', () => {
    const b = browserFactory.create('chromium', { provider: 'chromium', headless: true, viewport: { width: 1280, height: 720 }, userAgent: null, locale: null, timezoneId: null, geolocation: null, deviceScaleFactor: 1, ignoreHttpsErrors: false, extraArgs: [], proxy: null, downloadPath: null, recordVideo: false, tracesDir: null, screenshotsDir: null })
    expect(b.id).toMatch(/^brw_/)
    expect(b.provider).toBe('chromium')
    expect(b.status).toBe('idle')
    expect(b.metrics.pageLoads).toBe(0)
  })

  it('lists all browsers', () => {
    browserFactory.create('chromium', {} as BrowserConfig)
    browserFactory.create('firefox', {} as BrowserConfig)
    expect(browserFactory.listAll()).toHaveLength(2)
  })

  it('gets a browser by id', () => {
    const b = browserFactory.create('chromium', {} as BrowserConfig)
    expect(browserFactory.get(b.id)?.id).toBe(b.id)
  })

  it('updates browser state', () => {
    const b = browserFactory.create('chromium', {} as BrowserConfig)
    browserFactory.update(b.id, { status: 'running' })
    expect(browserFactory.get(b.id)?.status).toBe('running')
  })

  it('removes a browser', () => {
    const b = browserFactory.create('chromium', {} as BrowserConfig)
    browserFactory.remove(b.id)
    expect(browserFactory.get(b.id)).toBeUndefined()
  })

  it('updates metrics', () => {
    const b = browserFactory.create('chromium', {} as BrowserConfig)
    browserFactory.updateMetrics(b.id, { pageLoads: 5, actions: 10 })
    expect(browserFactory.get(b.id)?.metrics.pageLoads).toBe(5)
    expect(browserFactory.get(b.id)?.metrics.actions).toBe(10)
  })

  it('counts active browsers', () => {
    const b = browserFactory.create('chromium', {} as BrowserConfig)
    browserFactory.update(b.id, { status: 'running' })
    browserFactory.create('firefox', {} as BrowserConfig)
    expect(browserFactory.getActiveCount()).toBe(1)
  })
})

describe('sessionManager', () => {
  it('creates a session', () => {
    const b = browserFactory.create('chromium', {} as BrowserConfig)
    const s = sessionManager.create(b.id)
    expect(s.id).toMatch(/^sess_/)
    expect(s.status).toBe('active')
    expect(s.browserId).toBe(b.id)
  })

  it('lists sessions by browser', () => {
    const b = browserFactory.create('chromium', {} as BrowserConfig)
    sessionManager.create(b.id)
    sessionManager.create(b.id)
    expect(sessionManager.listByBrowser(b.id)).toHaveLength(2)
  })

  it('updates session status', () => {
    const b = browserFactory.create('chromium', {} as BrowserConfig)
    const s = sessionManager.create(b.id)
    sessionManager.pause(b.id, s.id)
    expect(sessionManager.get(b.id, s.id)?.status).toBe('paused')
    sessionManager.resume(b.id, s.id)
    expect(sessionManager.get(b.id, s.id)?.status).toBe('active')
    sessionManager.close(b.id, s.id)
    expect(sessionManager.get(b.id, s.id)?.status).toBe('closed')
  })

  it('manages tabs', () => {
    const b = browserFactory.create('chromium', {} as BrowserConfig)
    const s = sessionManager.create(b.id)
    sessionManager.addTab(b.id, s.id, { id: 'tab1', url: 'https://example.com', title: 'Example', status: 'ready', createdAt: new Date().toISOString() })
    expect(sessionManager.get(b.id, s.id)?.tabs).toHaveLength(1)
    sessionManager.closeTab(b.id, s.id, 'tab1')
    expect(sessionManager.get(b.id, s.id)?.tabs).toHaveLength(0)
  })

  it('gets active sessions', () => {
    const b = browserFactory.create('chromium', {} as BrowserConfig)
    sessionManager.create(b.id)
    expect(sessionManager.getActiveSessions()).toHaveLength(1)
  })
})

describe('navigationEngine', () => {
  it('navigates to a URL', async () => {
    const result = await navigationEngine.navigate('https://example.com', 'sess1', { retries: 1, timeout: 5000 })
    expect(result.url).toBe('https://example.com')
    expect(result.status).toMatch(/success|timeout|error/)
    expect(result.duration).toBeGreaterThanOrEqual(0)
    expect(result.timestamp).toBeTruthy()
  })

  it('handles invalid URLs', async () => {
    const result = await navigationEngine.navigate('not-a-url', 'sess1', { retries: 0 })
    expect(result.error).toBeTruthy()
    expect(result.status).toBe('error')
  })

  it('stores navigation history', async () => {
    await navigationEngine.navigate('https://example.com', 'sess1', { retries: 1, timeout: 5000 })
    const history = navigationEngine.getHistory('sess1')
    expect(history).toHaveLength(1)
    expect(history[0].url).toBe('https://example.com')
  })

  it('clears history', async () => {
    await navigationEngine.navigate('https://example.com', 'sess1', { retries: 1, timeout: 5000 })
    navigationEngine.clearHistory('sess1')
    expect(navigationEngine.getHistory('sess1')).toHaveLength(0)
  })

  it('gets latest navigation', async () => {
    await navigationEngine.navigate('https://example.com', 'sess1', { retries: 1, timeout: 5000 })
    expect(navigationEngine.getLatest('sess1')).not.toBeNull()
  })

  it('validates URLs', () => {
    expect(navigationEngine.isValidUrl('https://example.com')).toBe(true)
    expect(navigationEngine.isValidUrl('not-a-url')).toBe(false)
  })
})

describe('domInspectionService', () => {
  it('classifies elements', () => {
    expect(domInspectionService.classifyElement('input', { type: 'text' })).toBe('input')
    expect(domInspectionService.classifyElement('button', {})).toBe('button')
    expect(domInspectionService.classifyElement('a', {})).toBe('link')
    expect(domInspectionService.classifyElement('input', { type: 'checkbox' })).toBe('checkbox')
    expect(domInspectionService.classifyElement('input', { type: 'file' })).toBe('file')
    expect(domInspectionService.classifyElement('select', {})).toBe('dropdown')
    expect(domInspectionService.classifyElement('textarea', {})).toBe('textarea')
    expect(domInspectionService.classifyElement('form', {})).toBe('form')
    expect(domInspectionService.classifyElement('iframe', {})).toBe('iframe')
  })

  it('creates element snapshots', () => {
    const el = domInspectionService.createElementSnapshot('input', { type: 'text', name: 'email', placeholder: 'Email' }, null)
    expect(el.tag).toBe('input')
    expect(el.name).toBe('email')
    expect(el.type).toBe('input')
  })

  it('detects forms from elements', () => {
    const form = domInspectionService.createElementSnapshot('form', { id: 'form1', action: '/submit', method: 'post' }, null)
    const input = domInspectionService.createElementSnapshot('input', { type: 'text', name: 'username' }, null)
    const btn = domInspectionService.createElementSnapshot('button', { type: 'submit' }, 'Submit')
    const detected = domInspectionService.detectForm([form, input, btn])
    expect(detected).not.toBeNull()
    expect(detected?.formId).toBe('form1')
    expect(detected?.method).toBe('POST')
  })

  it('extracts aria attributes', () => {
    const el = domInspectionService.createElementSnapshot('div', { 'aria-label': 'Close', 'aria-hidden': 'true', class: 'btn' }, 'X')
    expect(el.aria).toEqual({ 'aria-label': 'Close', 'aria-hidden': 'true' })
  })
})

describe('actionEngine', () => {
  it('clicks an element', async () => {
    const el: DOMElement = { tag: 'button', type: 'button', attributes: {}, text: 'Click', rect: null, visible: true, enabled: true, readonly: false, checked: null, selected: null, value: null, name: null, id: null, classes: [], aria: null, children: [], shadowRoot: false, iframeContent: null }
    const result = await actionEngine.click(el, 'sess1')
    expect(result).toBe(true)
  })

  it('fails on disabled element', async () => {
    const el: DOMElement = { tag: 'button', type: 'button', attributes: { disabled: 'true' }, text: 'Disabled', rect: null, visible: true, enabled: false, readonly: false, checked: null, selected: null, value: null, name: null, id: null, classes: [], aria: null, children: [], shadowRoot: false, iframeContent: null }
    const result = await actionEngine.click(el, 'sess1')
    expect(result).toBe(false)
  })

  it('types text', async () => {
    const el: DOMElement = { tag: 'input', type: 'input', attributes: {}, text: null, rect: null, visible: true, enabled: true, readonly: false, checked: null, selected: null, value: null, name: null, id: null, classes: [], aria: null, children: [], shadowRoot: false, iframeContent: null }
    const result = await actionEngine.type(el, 'hello', 'sess1')
    expect(result).toBe(true)
  })

  it('fails type on readonly element', async () => {
    const el: DOMElement = { tag: 'input', type: 'input', attributes: { readonly: 'true' }, text: null, rect: null, visible: true, enabled: true, readonly: true, checked: null, selected: null, value: null, name: null, id: null, classes: [], aria: null, children: [], shadowRoot: false, iframeContent: null }
    const result = await actionEngine.type(el, 'hello', 'sess1')
    expect(result).toBe(false)
  })

  it('stores action history', async () => {
    const el: DOMElement = { tag: 'button', type: 'button', attributes: {}, text: 'Test', rect: null, visible: true, enabled: true, readonly: false, checked: null, selected: null, value: null, name: null, id: null, classes: [], aria: null, children: [], shadowRoot: false, iframeContent: null }
    await actionEngine.click(el, 'sess2')
    const history = actionEngine.getHistory('sess2')
    expect(history).toHaveLength(1)
    expect(history[0].type).toBe('click')
    expect(history[0].success).toBe(true)
  })

  it('clears action history', () => {
    actionEngine.clearHistory('sess1')
    expect(actionEngine.getHistory('sess1')).toHaveLength(0)
  })
})

describe('locatorEngine', () => {
  it('finds an element by selector', async () => {
    const el = await locatorEngine.findElement('#my-button', 'css')
    expect(el).not.toBeNull()
    expect(el?.tag).toBe('div')
  })

  it('finds elements by selector', async () => {
    const els = await locatorEngine.findElements('.item', 'css')
    expect(els.length).toBe(3)
  })

  it('waits for element', async () => {
    const el = await locatorEngine.waitForElement('#test', 'css', 1000)
    expect(el).not.toBeNull()
  })

  it('waits for element to disappear', async () => {
    const result = await locatorEngine.waitForElementToDisappear('#test', 'css', 100)
    expect(result).toBe(false)
  })

  it('finds by text', async () => {
    const el = await locatorEngine.findByText('Some text')
    expect(el?.text).toBe('Some text')
  })
})

describe('humanBehaviourService', () => {
  it('provides typing delay', () => {
    const delay = humanBehaviourService.getTypingDelay()
    expect(delay).toBeGreaterThanOrEqual(50)
    expect(delay).toBeLessThanOrEqual(200)
  })

  it('provides mouse delay', () => {
    expect(humanBehaviourService.getMouseDelay()).toBeGreaterThan(0)
  })

  it('randomizes typing when enabled', () => {
    const result = humanBehaviourService.randomizeTyping('hello')
    expect(result.length).toBe(5)
  })

  it('does not randomize typing when disabled', () => {
    humanBehaviourService.updateConfig({ randomMistakes: false })
    expect(humanBehaviourService.randomizeTyping('hello')).toBe('hello')
  })

  it('can update and reset config', () => {
    humanBehaviourService.updateConfig({ errorRate: 0.5, enabled: false })
    expect(humanBehaviourService.config.errorRate).toBe(0.5)
    expect(humanBehaviourService.config.enabled).toBe(false)
    humanBehaviourService.resetConfig()
    expect(humanBehaviourService.config.enabled).toBe(true)
  })
})

describe('errorRecoveryService', () => {
  it('retries a function on failure', async () => {
    let calls = 0
    const fn = async () => {
      calls++
      if (calls < 3) throw new Error('fail')
      return 'success'
    }
    const result = await errorRecoveryService.retry(fn, () => true, { maxRetries: 3, baseDelay: 10 })
    expect(result).toBe('success')
    expect(calls).toBe(3)
  })

  it('throws after exhausting retries', async () => {
    const fn = async () => { throw new Error('always fail') }
    await expect(errorRecoveryService.retry(fn, () => true, { maxRetries: 2, baseDelay: 10 })).rejects.toThrow('always fail')
  })

  it('can update config', () => {
    errorRecoveryService.updateConfig({ maxRetries: 5 })
    expect(errorRecoveryService.config.maxRetries).toBe(5)
    errorRecoveryService.resetConfig()
    expect(errorRecoveryService.config.maxRetries).toBe(3)
  })

  it('detects error types', () => {
    expect(errorRecoveryService.isStaleElementError(new Error('stale element'))).toBe(true)
    expect(errorRecoveryService.isTimeoutError(new Error('timeout exceeded'))).toBe(true)
    expect(errorRecoveryService.isNavigationError(new Error('navigation failed'))).toBe(true)
    expect(errorRecoveryService.isStaleElementError(new Error('generic error'))).toBe(false)
  })
})

describe('monitoringService', () => {
  it('generates a report for a browser', () => {
    const b = browserFactory.create('chromium', {} as BrowserConfig)
    const report = monitoringService.generateReport(b.id)
    expect(report.browserId).toBe(b.id)
    expect(report.sessions).toBe(0)
    expect(report.successRate).toBe(100)
  })

  it('generates reports for all browsers', () => {
    browserFactory.create('chromium', {} as BrowserConfig)
    browserFactory.create('firefox', {} as BrowserConfig)
    expect(monitoringService.getAllReports()).toHaveLength(2)
  })

  it('reports overall health', () => {
    browserFactory.create('chromium', {} as BrowserConfig)
    const health = monitoringService.getOverallHealth()
    expect(health.ok).toBe(true)
    expect(health.activeBrowsers).toBe(0)
  })
})

describe('screenshotService', () => {
  it('captures a screenshot', async () => {
    const result = await screenshotService.capture('sess1', 'https://example.com')
    expect(result.id).toMatch(/^ss_/)
    expect(result.url).toBe('https://example.com')
    expect(result.filename).toMatch(/\.png$/)
  })

  it('captures element screenshot', async () => {
    const result = await screenshotService.captureElement('sess1', 'https://example.com', '#my-element')
    expect(result.type).toBe('element')
  })

  it('stores and retrieves history', async () => {
    await screenshotService.capture('sess1', 'https://example.com')
    expect(screenshotService.getHistory('sess1')).toHaveLength(1)
  })

  it('deletes a screenshot', async () => {
    const s = await screenshotService.capture('sess1', 'https://example.com')
    screenshotService.delete('sess1', s.id)
    expect(screenshotService.getHistory('sess1')).toHaveLength(0)
  })

  it('clears all screenshots', async () => {
    await screenshotService.capture('sess1', 'https://example.com')
    screenshotService.clearAll('sess1')
    expect(screenshotService.getHistory('sess1')).toHaveLength(0)
  })
})

describe('downloadService', () => {
  it('downloads a file', async () => {
    const result = await downloadService.download('https://example.com/file.pdf', 'sess1')
    expect(result.id).toMatch(/^dl_/)
    expect(result.filename).toMatch(/\.pdf$/)
    expect(result.mimeType).toBe('application/pdf')
  })

  it('guesses extension from URL', () => {
    expect(downloadService.guessExtension('https://example.com/file.pdf')).toBe('.pdf')
    expect(downloadService.guessExtension('https://example.com/file')).toBe('.bin')
  })

  it('stores history', async () => {
    await downloadService.download('https://example.com/doc.docx', 'sess1')
    expect(downloadService.getHistory('sess1')).toHaveLength(1)
  })
})

describe('loggingService', () => {
  it('logs entries at different levels', () => {
    loggingService.info('sess1', 'test', 'info message')
    loggingService.warn('sess1', 'test', 'warn message')
    loggingService.error('sess1', 'test', 'error message')
    expect(loggingService.getRecent('sess1')).toHaveLength(3)
  })

  it('filters by level', () => {
    loggingService.info('sess1', 'test', 'info')
    loggingService.error('sess1', 'test', 'error1')
    loggingService.error('sess1', 'test', 'error2')
    expect(loggingService.getErrors('sess1')).toHaveLength(2)
    expect(loggingService.getWarnings('sess1')).toHaveLength(0)
  })

  it('clears logs', () => {
    loggingService.info('sess1', 'test', 'msg')
    loggingService.clear('sess1')
    expect(loggingService.getRecent('sess1')).toHaveLength(0)
  })

  it('increments browser error count on error logs', () => {
    const b = browserFactory.create('chromium', {} as BrowserConfig)
    const s = sessionManager.create(b.id)
    loggingService.error(s.id, 'test', 'err')
    expect(browserFactory.get(b.id)?.metrics.errors).toBeGreaterThan(0)
  })
})
