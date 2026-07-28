import type { JobProvider, ProviderConfig, ProviderId, ProviderCapability } from './types'
import { linkedinProvider } from './providers/linkedin'
import { indeedProvider } from './providers/indeed'
import { naukriProvider } from './providers/naukri'
import { founditProvider } from './providers/foundit'
import { wellfoundProvider } from './providers/wellfound'
import { ycombinatorProvider } from './providers/ycombinator'
import { companyCareersProvider } from './providers/company-careers'
import { internshalaProvider } from './providers/internshala'
import { unstopProvider } from './providers/unstop'
import { freshersworldProvider } from './providers/freshersworld'
import { greenhouseProvider } from '../ats/providers/greenhouse'
import { leverProvider } from '../ats/providers/lever'
import { ashbyProvider } from '../ats/providers/ashby'
import { smartrecruitersProvider } from '../ats/providers/smartrecruiters'

const PREFIX = 'ajapp_disc_'

function get<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(PREFIX + key)
    return raw ? JSON.parse(raw) : fallback
  } catch { return fallback }
}

function set<T>(key: string, value: T): void {
  try { localStorage.setItem(PREFIX + key, JSON.stringify(value)) } catch {}
}

const DEFAULT_PROVIDERS: JobProvider[] = [
  linkedinProvider,
  indeedProvider,
  naukriProvider,
  founditProvider,
  wellfoundProvider,
  ycombinatorProvider,
  companyCareersProvider,
  internshalaProvider,
  unstopProvider,
  freshersworldProvider,
  greenhouseProvider,
  leverProvider,
  ashbyProvider,
  smartrecruitersProvider,
]

export const providerRegistry = {
  getAll(): JobProvider[] {
    const configs = get<ProviderConfig[]>('provider_configs', [])
    if (configs.length === 0) {
      const defaults = DEFAULT_PROVIDERS.map(p => ({
        id: p.id,
        name: p.name,
        enabled: p.enabled,
        priority: p.priority,
        capabilities: p.capabilities,
        baseUrl: null as string | null,
        apiKeyRequired: false,
        apiKeyConfigured: false,
      }))
      set('provider_configs', defaults)
      return DEFAULT_PROVIDERS
    }
    return DEFAULT_PROVIDERS.map(dp => {
      const config = configs.find(c => c.id === dp.id)
      if (config) {
        return { ...dp, enabled: config.enabled, priority: config.priority }
      }
      return dp
    })
  },

  get(id: ProviderId): JobProvider | undefined {
    return this.getAll().find(p => p.id === id)
  },

  getEnabled(): JobProvider[] {
    return this.getAll().filter(p => p.enabled)
  },

  register(provider: JobProvider): void {
    const configs = get<ProviderConfig[]>('provider_configs', [])
    configs.push({
      id: provider.id,
      name: provider.name,
      enabled: provider.enabled,
      priority: provider.priority,
      capabilities: provider.capabilities,
      baseUrl: null,
      apiKeyRequired: false,
      apiKeyConfigured: false,
    })
    set('provider_configs', configs)
  },

  remove(id: ProviderId): void {
    const configs = get<ProviderConfig[]>('provider_configs', [])
    set('provider_configs', configs.filter(c => c.id !== id))
  },

  enable(id: ProviderId): void {
    this.updateConfig(id, { enabled: true })
  },

  disable(id: ProviderId): void {
    this.updateConfig(id, { enabled: false })
  },

  setPriority(id: ProviderId, priority: number): void {
    this.updateConfig(id, { priority })
  },

  updateConfig(id: ProviderId, updates: Partial<ProviderConfig>): void {
    let configs = get<ProviderConfig[]>('provider_configs', [])
    if (configs.length === 0) {
      for (const p of DEFAULT_PROVIDERS) {
        configs.push({
          id: p.id, name: p.name, enabled: p.enabled, priority: p.priority,
          capabilities: p.capabilities, baseUrl: null, apiKeyRequired: false, apiKeyConfigured: false,
        })
      }
    }
    const idx = configs.findIndex(c => c.id === id)
    if (idx !== -1) {
      configs[idx] = { ...configs[idx], ...updates }
      set('provider_configs', configs)
    }
  },

  getConfigs(): ProviderConfig[] {
    return get<ProviderConfig[]>('provider_configs', [])
  },

  getCapabilities(): ProviderCapability[] {
    const all = new Set<ProviderCapability>()
    for (const p of this.getEnabled()) {
      for (const c of p.capabilities) all.add(c)
    }
    return [...all]
  },

  hasCapability(capability: ProviderCapability): boolean {
    return this.getEnabled().some(p => p.capabilities.includes(capability))
  },

  getByCapability(capability: ProviderCapability): JobProvider[] {
    return this.getEnabled().filter(p => p.capabilities.includes(capability))
  },

  getPrioritized(): JobProvider[] {
    return this.getEnabled().sort((a, b) => a.priority - b.priority)
  },
}
