import type { AuthMethodType, ValidationResult } from './types'
import type { AuthenticationStrategy } from './strategies/base-strategy'
import { getDefaultStrategies } from './strategies'

let strategies = new Map<string, AuthenticationStrategy>()
let initialized = false

function ensureInitialized(): void {
  if (!initialized) {
    for (const s of getDefaultStrategies()) {
      strategies.set(s.id, s)
    }
    initialized = true
  }
}

export const authenticationRegistry = {
  register(strategy: AuthenticationStrategy): void {
    ensureInitialized()
    if (strategies.has(strategy.id)) {
      throw new Error(`Strategy '${strategy.id}' is already registered`)
    }
    strategies.set(strategy.id, strategy)
  },

  unregister(strategyId: string): boolean {
    ensureInitialized()
    return strategies.delete(strategyId)
  },

  get(strategyId: string): AuthenticationStrategy | undefined {
    ensureInitialized()
    return strategies.get(strategyId)
  },

  getByMethod(method: AuthMethodType): AuthenticationStrategy[] {
    ensureInitialized()
    return Array.from(strategies.values()).filter(s => s.method === method)
  },

  getAll(): AuthenticationStrategy[] {
    ensureInitialized()
    return Array.from(strategies.values())
  },

  resolve(method: AuthMethodType): AuthenticationStrategy | undefined {
    ensureInitialized()
    const byMethod = this.getByMethod(method)
    if (byMethod.length > 0) return byMethod[0]
    return strategies.get(method)
  },

  getDefault(): AuthenticationStrategy | undefined {
    ensureInitialized()
    return strategies.get('username_password') ?? strategies.values().next().value
  },

  validateStrategy(strategyId: string, config: Record<string, unknown>): ValidationResult {
    ensureInitialized()
    const strategy = strategies.get(strategyId)
    if (!strategy) return { valid: false, errors: [{ field: 'strategyId', message: `Strategy '${strategyId}' not found`, code: 'STRATEGY_NOT_FOUND' }] }
    return strategy.validateConfig(config)
  },

  discover(method?: AuthMethodType): AuthenticationStrategy[] {
    ensureInitialized()
    if (method) return this.getByMethod(method)
    return this.getAll()
  },

  getCount(): number {
    ensureInitialized()
    return strategies.size
  },

  reset(): void {
    strategies.clear()
    initialized = false
  },
}
