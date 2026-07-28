import type { ProviderMetadata, CapabilityId, ProviderConfiguration } from './types'
import { capabilitySystem } from './capability-system'

interface RegisteredProvider {
  metadata: ProviderMetadata
  instance: unknown
  registeredAt: string
  configuration: ProviderConfiguration
}

const PREFIX = 'ajapp_sdk_reg_'

function get<T>(key: string, fallback: T): T {
  try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback } catch { return fallback }
}
function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

let providers = new Map<string, RegisteredProvider>()
let listeners: Array<(event: string, providerId: string, metadata?: ProviderMetadata) => void> = []

function persist(): void {
  const configs: ProviderConfiguration[] = []
  for (const provider of providers.values()) {
    configs.push(provider.configuration)
  }
  set(PREFIX + 'configs', configs)
}

function loadPersisted(): void {
  const configs = get<ProviderConfiguration[]>(PREFIX + 'configs', [])
  for (const config of configs) {
    const existing = providers.get(config.id)
    if (existing) {
      existing.configuration = config
    }
  }
}

export const providerRegistry = {
  register(metadata: ProviderMetadata, instance: unknown, config?: Partial<ProviderConfiguration>): void {
    if (providers.has(metadata.id)) {
      throw new Error(`Provider '${metadata.id}' is already registered`)
    }
    const configuration: ProviderConfiguration = {
      id: metadata.id,
      enabled: true,
      priority: 100,
      config: {},
      pipeline: {
        retry: { maxRetries: 3, baseDelayMs: 1000, maxDelayMs: 10000, retryableErrors: ['RATE_LIMIT_ERROR', 'TIMEOUT_ERROR', 'PROVIDER_UNAVAILABLE_ERROR'] },
        cache: { enabled: true, ttlMs: 300000, maxEntries: 500 },
        timeoutMs: 30000,
        validateResponse: true,
      },
      metadata,
      ...config,
    }
    providers.set(metadata.id, {
      metadata,
      instance,
      registeredAt: new Date().toISOString(),
      configuration,
    })
    persist()
    for (const listener of listeners) listener('registered', metadata.id, metadata)
  },

  unregister(providerId: string): boolean {
    const removed = providers.delete(providerId)
    if (removed) {
      persist()
      for (const listener of listeners) listener('unregistered', providerId)
    }
    return removed
  },

  get(providerId: string): RegisteredProvider | undefined {
    return providers.get(providerId)
  },

  getInstance<T>(providerId: string): T | undefined {
    return providers.get(providerId)?.instance as T | undefined
  },

  getAll(): RegisteredProvider[] {
    return Array.from(providers.values())
  },

  getByCapability(capability: CapabilityId): RegisteredProvider[] {
    return Array.from(providers.values()).filter(p =>
      capabilitySystem.hasCapability(p.metadata.capabilities, capability) && p.configuration.enabled
    )
  },

  getByCapabilities(capabilities: CapabilityId[], match: 'all' | 'any' = 'any'): RegisteredProvider[] {
    return Array.from(providers.values()).filter(p => {
      if (!p.configuration.enabled) return false
      return match === 'all'
        ? capabilitySystem.hasAllCapabilities(p.metadata.capabilities, capabilities)
        : capabilitySystem.hasAnyCapability(p.metadata.capabilities, capabilities)
    })
  },

  getEnabled(): RegisteredProvider[] {
    return Array.from(providers.values()).filter(p => p.configuration.enabled)
  },

  getPrioritized(): RegisteredProvider[] {
    return this.getEnabled().sort((a, b) => a.configuration.priority - b.configuration.priority)
  },

  enable(providerId: string): void {
    const provider = providers.get(providerId)
    if (provider) {
      provider.configuration.enabled = true
      persist()
    }
  },

  disable(providerId: string): void {
    const provider = providers.get(providerId)
    if (provider) {
      provider.configuration.enabled = false
      persist()
    }
  },

  updateConfig(providerId: string, updates: Partial<ProviderConfiguration>): void {
    const provider = providers.get(providerId)
    if (provider) {
      provider.configuration = { ...provider.configuration, ...updates }
      persist()
    }
  },

  getConfig(providerId: string): ProviderConfiguration | undefined {
    return providers.get(providerId)?.configuration
  },

  getAllCapabilities(): CapabilityId[] {
    const all = new Set<CapabilityId>()
    for (const p of providers.values()) {
      for (const c of p.metadata.capabilities) all.add(c)
    }
    return [...all]
  },

  hasCapability(capability: CapabilityId): boolean {
    return Array.from(providers.values()).some(p =>
      p.configuration.enabled && capabilitySystem.hasCapability(p.metadata.capabilities, capability)
    )
  },

  getCount(): number {
    return providers.size
  },

  getEnabledCount(): number {
    return this.getEnabled().length
  },

  onChange(listener: (event: string, providerId: string, metadata?: ProviderMetadata) => void): () => void {
    listeners.push(listener)
    return () => {
      const idx = listeners.indexOf(listener)
      if (idx !== -1) listeners.splice(idx, 1)
    }
  },

  loadFromPersisted(): void {
    loadPersisted()
  },

  reset(): void {
    providers.clear()
    localStorage.removeItem(PREFIX + 'configs')
  },
}
