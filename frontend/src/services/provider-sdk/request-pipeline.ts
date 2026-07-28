import type { ProviderContext, PipelineResult, CacheEntry } from './types'
import { ProviderError, TimeoutError, isRecoverableError } from './errors'
import { nowISO } from '../orchestration/utils'

const DEFAULT_RETRY_CONFIG = { maxRetries: 3, baseDelayMs: 1000, maxDelayMs: 10000, retryableErrors: ['RATE_LIMIT_ERROR', 'TIMEOUT_ERROR', 'PROVIDER_UNAVAILABLE_ERROR'] }
const DEFAULT_CACHE_CONFIG = { enabled: true, ttlMs: 300000, maxEntries: 500 }

function getCacheKey(providerId: string, operation: string, params: unknown): string {
  return `ajapp_sdk_cache_${providerId}_${operation}_${JSON.stringify(params)}`
}

interface InternalState {
  cache: Map<string, CacheEntry<unknown>>
  hooks: PipelineHook[]
}

interface PipelineHook {
  beforeExecute?: <T>(input: T, ctx: ProviderContext) => Promise<T>
  afterExecute?: <T>(result: PipelineResult<T>, ctx: ProviderContext) => Promise<PipelineResult<T>>
  onError?: (error: Error, ctx: ProviderContext) => Promise<void>
}

const state: InternalState = {
  cache: new Map(),
  hooks: [],
}

function computeDelay(attempt: number, baseMs: number, maxMs: number): number {
  const delay = Math.min(baseMs * Math.pow(2, attempt - 1), maxMs)
  return delay + Math.random() * delay * 0.1
}

async function executeWithTimeout<T>(
  fn: () => Promise<T>,
  timeoutMs: number,
  operation: string
): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new TimeoutError(`${operation} timed out after ${timeoutMs}ms`))
    }, timeoutMs)
    fn().then(
      (val) => { clearTimeout(timer); resolve(val) },
      (err) => { clearTimeout(timer); reject(err) }
    )
  })
}

export const requestPipeline = {
  addHook(hook: PipelineHook): void {
    state.hooks.push(hook)
  },

  removeHook(hook: PipelineHook): void {
    const idx = state.hooks.indexOf(hook)
    if (idx !== -1) state.hooks.splice(idx, 1)
  },

  async execute<T>(
    operation: string,
    params: unknown,
    executeFn: (ctx: ProviderContext) => Promise<T>,
    ctx: ProviderContext,
    overrides?: { retry?: typeof DEFAULT_RETRY_CONFIG; cache?: typeof DEFAULT_CACHE_CONFIG; timeoutMs?: number }
  ): Promise<PipelineResult<T>> {
    const retryConfig = overrides?.retry ?? DEFAULT_RETRY_CONFIG
    const cacheConfig = overrides?.cache ?? DEFAULT_CACHE_CONFIG
    const timeoutMs = overrides?.timeoutMs ?? 30000
    const startTime = Date.now()

    if (cacheConfig.enabled && operation === 'search') {
      const cacheKey = getCacheKey(ctx.providerId, operation, params)
      const cached = state.cache.get(cacheKey) as CacheEntry<T> | undefined
      if (cached && cached.expiresAt > Date.now()) {
        return { success: true, data: cached.data, duration: 0, attempts: 1, cached: true }
      }
    }

    let attempts = 0
    let lastError: Error | undefined

    while (attempts <= retryConfig.maxRetries) {
      attempts++
      try {
        let input = { ctx } as any
        for (const hook of state.hooks) {
          if (hook.beforeExecute) input = await hook.beforeExecute(input, ctx)
        }

        const result = await executeWithTimeout(() => executeFn(ctx), timeoutMs, operation)

        let pipelineResult: PipelineResult<T> = {
          success: true,
          data: result,
          duration: Date.now() - startTime,
          attempts,
          cached: false,
        }

        for (const hook of state.hooks) {
          if (hook.afterExecute) pipelineResult = await hook.afterExecute(pipelineResult, ctx)
        }

        if (cacheConfig.enabled && operation === 'search' && pipelineResult.data) {
          const cacheKey = getCacheKey(ctx.providerId, operation, params)
          state.cache.set(cacheKey, {
            data: pipelineResult.data,
            expiresAt: Date.now() + cacheConfig.ttlMs,
            createdAt: nowISO(),
          } as CacheEntry<unknown>)
          if (state.cache.size > cacheConfig.maxEntries) {
            const firstKey = state.cache.keys().next().value
            if (firstKey) state.cache.delete(firstKey)
          }
        }

        return pipelineResult
      } catch (err) {
        lastError = err instanceof Error ? err : new Error(String(err))

        for (const hook of state.hooks) {
          if (hook.onError) await hook.onError(lastError, ctx)
        }

        const isRetryable = isRecoverableError(lastError) || lastError instanceof TimeoutError
        if (!isRetryable || attempts > retryConfig.maxRetries) {
          return {
            success: false,
            error: lastError,
            duration: Date.now() - startTime,
            attempts,
            cached: false,
          }
        }

        const delay = computeDelay(attempts, retryConfig.baseDelayMs, retryConfig.maxDelayMs)
        await new Promise(resolve => setTimeout(resolve, delay))
      }
    }

    return {
      success: false,
      error: lastError ?? new ProviderError('Max retries exceeded', 'MAX_RETRIES_EXCEEDED', ctx.providerId, false),
      duration: Date.now() - startTime,
      attempts,
      cached: false,
    }
  },

  clearCache(): void {
    state.cache.clear()
  },

  invalidateCache(providerId?: string): void {
    if (!providerId) {
      this.clearCache()
      return
    }
    for (const key of state.cache.keys()) {
      if (key.includes(`ajapp_sdk_cache_${providerId}_`)) state.cache.delete(key)
    }
  },
}
