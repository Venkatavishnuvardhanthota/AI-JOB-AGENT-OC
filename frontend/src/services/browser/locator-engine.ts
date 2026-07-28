import type { LocatorOptions, LocatorStrategy, DOMElement } from './types'
import { DEFAULT_LOCATOR_OPTIONS } from './types'
import { sleep } from './utils'

export const locatorEngine = {
  async findElement(
    selector: string,
    strategy: LocatorStrategy = 'css',
    options: Partial<LocatorOptions> = {}
  ): Promise<DOMElement | null> {
    const opts = { ...DEFAULT_LOCATOR_OPTIONS, ...options, strategy }
    return this.executeWithRetry(`find_${strategy}`, selector, opts, () => {
      const element = this.simulateFind(selector, strategy, opts)
      if (!element) return null
      if (opts.visible && !element.visible) return null
      if (opts.enabled && !element.enabled) return null
      return element
    })
  },

  async findElements(
    selector: string,
    strategy: LocatorStrategy = 'css',
    options: Partial<LocatorOptions> = {}
  ): Promise<DOMElement[]> {
    const opts = { ...DEFAULT_LOCATOR_OPTIONS, ...options, strategy }
    return this.executeWithRetry(`findAll_${strategy}`, selector, opts, () => {
      return this.simulateFindAll(selector, strategy, opts)
    })
  },

  async waitForElement(
    selector: string,
    strategy: LocatorStrategy = 'css',
    timeout: number = 10000
  ): Promise<DOMElement | null> {
    const start = Date.now()
    while (Date.now() - start < timeout) {
      const element = await this.findElement(selector, strategy, { timeout, waitForElement: true })
      if (element) return element
      await sleep(200)
    }
    return null
  },

  async waitForElementToDisappear(
    selector: string,
    strategy: LocatorStrategy = 'css',
    timeout: number = 10000
  ): Promise<boolean> {
    const start = Date.now()
    while (Date.now() - start < timeout) {
      const element = await this.findElement(selector, strategy, { timeout: 1000, waitForElement: false })
      if (!element) return true
      await sleep(200)
    }
    return false
  },

  async findByText(text: string, options: Partial<LocatorOptions> = {}): Promise<DOMElement | null> {
    return this.findElement(text, 'text', options)
  },

  async findByLabel(label: string, options: Partial<LocatorOptions> = {}): Promise<DOMElement | null> {
    return this.findElement(label, 'label', options)
  },

  async findByPlaceholder(placeholder: string, options: Partial<LocatorOptions> = {}): Promise<DOMElement | null> {
    return this.findElement(placeholder, 'placeholder', options)
  },

  async findByRole(role: string, options: Partial<LocatorOptions> = {}): Promise<DOMElement | null> {
    return this.findElement(role, 'role', options)
  },

  async findByTestId(testId: string, options: Partial<LocatorOptions> = {}): Promise<DOMElement | null> {
    return this.findElement(testId, 'test_id', options)
  },

  async executeWithRetry<T>(
    _operation: string,
    _selector: string,
    options: LocatorOptions,
    action: () => T
  ): Promise<T> {
    let lastError: Error | null = null
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        if (options.waitForElement && attempt > 0) {
          await sleep(500 * attempt)
        }
        return action()
      } catch (err) {
        lastError = err instanceof Error ? err : new Error(String(err))
        if (attempt < 2) await sleep(300)
      }
    }
    throw lastError
  },

  simulateFind(selector: string, strategy: LocatorStrategy, _options: LocatorOptions): DOMElement | null {
    const mockElement: DOMElement = {
      tag: 'div',
      type: 'unknown',
      attributes: {
        id: strategy === 'test_id' ? selector : '',
        class: '',
        'data-testid': strategy === 'test_id' ? selector : '',
        'aria-label': strategy === 'aria_label' ? selector : '',
        placeholder: strategy === 'placeholder' ? selector : '',
        role: strategy === 'role' ? selector : '',
      },
      text: strategy === 'text' ? selector : 'Mock content',
      rect: { x: 100, y: 200, width: 300, height: 40 },
      visible: true,
      enabled: true,
      readonly: false,
      checked: null,
      selected: null,
      value: null,
      name: null,
      id: strategy === 'test_id' ? selector : 'mock-id',
      classes: [],
      aria: null,
      children: [],
      shadowRoot: false,
      iframeContent: null,
    }
    return mockElement
  },

  simulateFindAll(_selector: string, _strategy: LocatorStrategy, _options: LocatorOptions): DOMElement[] {
    const elements: DOMElement[] = []
    for (let i = 0; i < 3; i++) {
      elements.push({
        tag: 'div',
        type: 'unknown',
        attributes: { class: 'mock', 'data-index': String(i) },
        text: `Item ${i + 1}`,
        rect: { x: 100, y: 200 + i * 50, width: 300, height: 40 },
        visible: true,
        enabled: true,
        readonly: false,
        checked: null,
        selected: null,
        value: null,
        name: null,
        id: `mock-${i}`,
        classes: ['mock'],
        aria: null,
        children: [],
        shadowRoot: false,
        iframeContent: null,
      })
    }
    return elements
  },
}
