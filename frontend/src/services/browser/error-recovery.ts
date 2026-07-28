import type { RetryConfig, NavigationResult } from './types'
import { DEFAULT_RETRY_CONFIG } from './types'
import { sleep } from './utils'

export const errorRecoveryService = {
  config: { ...DEFAULT_RETRY_CONFIG },

  updateConfig(updates: Partial<RetryConfig>): void {
    this.config = { ...this.config, ...updates }
  },

  resetConfig(): void {
    this.config = { ...DEFAULT_RETRY_CONFIG }
  },

  async retry<T>(
    fn: () => Promise<T>,
    shouldRetry: (error: unknown) => boolean = () => true,
    customConfig?: Partial<RetryConfig>
  ): Promise<T> {
    const cfg = { ...this.config, ...customConfig }
    let lastError: unknown

    for (let attempt = 1; attempt <= cfg.maxRetries; attempt++) {
      try {
        return await fn()
      } catch (err) {
        lastError = err
        if (attempt === cfg.maxRetries || !shouldRetry(err)) throw err
        const delay = Math.min(cfg.baseDelay * Math.pow(cfg.backoffFactor, attempt - 1), cfg.maxDelay)
        await sleep(delay)
      }
    }

    throw lastError
  },

  async recoverNavigation(
    fn: () => Promise<NavigationResult>,
    customConfig?: Partial<RetryConfig>
  ): Promise<NavigationResult> {
    return this.retry(fn, (err) => {
      const message = err instanceof Error ? err.message : ''
      return this.shouldRetryNavigation(message, customConfig)
    }, customConfig)
  },

  async recoverAction(
    fn: () => Promise<boolean>,
    customConfig?: Partial<RetryConfig>
  ): Promise<boolean> {
    try {
      return await this.retry(fn, () => true, customConfig)
    } catch {
      return false
    }
  },

  shouldRetryNavigation(errorMessage: string, customConfig?: Partial<RetryConfig>): boolean {
    const cfg = { ...this.config, ...customConfig }
    if (!cfg.retryOnTimeout && errorMessage.includes('timeout')) return false
    if (!cfg.retryOnNavigation && errorMessage.includes('navigation')) return false
    if (!cfg.retryOnStaleElement && errorMessage.includes('stale')) return false
    return true
  },

  isStaleElementError(error: unknown): boolean {
    const msg = error instanceof Error ? error.message.toLowerCase() : ''
    return msg.includes('stale') || msg.includes('detached') || msg.includes('not found')
  },

  isTimeoutError(error: unknown): boolean {
    const msg = error instanceof Error ? error.message.toLowerCase() : ''
    return msg.includes('timeout') || msg.includes('timed out')
  },

  isNavigationError(error: unknown): boolean {
    const msg = error instanceof Error ? error.message.toLowerCase() : ''
    return msg.includes('navigation') || msg.includes('net::err') || msg.includes('http')
  },
}
