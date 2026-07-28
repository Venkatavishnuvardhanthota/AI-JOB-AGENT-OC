import { RateLimitError, TimeoutError, ProviderUnavailableError, SearchError } from '../provider-sdk/errors'

interface RateLimitState {
  tokens: number
  lastRefill: number
  maxTokens: number
  refillInterval: number
}

const rateLimitStates = new Map<string, RateLimitState>()

function getRateLimiter(key: string, maxPerSecond: number): RateLimitState {
  let state = rateLimitStates.get(key)
  if (!state) {
    state = { tokens: maxPerSecond, lastRefill: Date.now(), maxTokens: maxPerSecond, refillInterval: 1000 }
    rateLimitStates.set(key, state)
  }
  return state
}

function refillTokens(state: RateLimitState): void {
  const now = Date.now()
  const elapsed = now - state.lastRefill
  const tokensToAdd = Math.floor(elapsed / state.refillInterval) * state.maxTokens
  if (tokensToAdd > 0) {
    state.tokens = Math.min(state.maxTokens, state.tokens + tokensToAdd)
    state.lastRefill = now
  }
}

async function acquireToken(key: string, maxPerSecond: number): Promise<void> {
  const state = getRateLimiter(key, maxPerSecond)
  for (let attempt = 0; attempt < 10; attempt++) {
    refillTokens(state)
    if (state.tokens >= 1) {
      state.tokens -= 1
      return
    }
    await new Promise(r => setTimeout(r, state.refillInterval / state.maxTokens))
  }
  throw new RateLimitError(`Rate limit exceeded for ${key}`)
}

function classifyHttpStatus(status: number, providerId: string): Error | null {
  if (status === 429) return new RateLimitError(`Rate limited by ${providerId}`, providerId)
  if (status === 502 || status === 503 || status === 504) return new ProviderUnavailableError(`${providerId} unavailable (${status})`, providerId)
  if (status >= 500) return new SearchError(`${providerId} server error (${status})`, providerId)
  if (status === 401 || status === 403) return new SearchError(`${providerId} access denied (${status})`, providerId)
  if (status === 404) return new SearchError(`${providerId} endpoint not found`, providerId)
  if (status >= 400) return new SearchError(`${providerId} request failed (${status})`, providerId)
  return null
}

export interface ATSHttpOptions {
  baseUrl: string
  providerId: string
  rateLimitPerSecond?: number
  timeoutMs?: number
  headers?: Record<string, string>
}

export async function atsFetch<T>(path: string, options: ATSHttpOptions, queryParams?: Record<string, string>): Promise<T> {
  if (options.rateLimitPerSecond) {
    await acquireToken(options.providerId, options.rateLimitPerSecond)
  }

  const url = new URL(path, options.baseUrl)
  if (queryParams) {
    for (const [k, v] of Object.entries(queryParams)) {
      if (v !== undefined && v !== '') url.searchParams.set(k, v)
    }
  }

  const controller = new AbortController()
  const timeoutMs = options.timeoutMs ?? 30000
  const timer = setTimeout(() => controller.abort(), timeoutMs)

  try {
    const response = await fetch(url.toString(), {
      signal: controller.signal,
      headers: { Accept: 'application/json', ...options.headers },
    })

    const error = classifyHttpStatus(response.status, options.providerId)
    if (error) throw error

    const text = await response.text()
    if (!text) return {} as T

    return JSON.parse(text) as T
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new TimeoutError(`${options.providerId} request timed out after ${timeoutMs}ms`, options.providerId)
    }
    if (err instanceof TypeError && err.message.includes('fetch')) {
      throw new ProviderUnavailableError(`${options.providerId} network error`, options.providerId)
    }
    throw err
  } finally {
    clearTimeout(timer)
  }
}
