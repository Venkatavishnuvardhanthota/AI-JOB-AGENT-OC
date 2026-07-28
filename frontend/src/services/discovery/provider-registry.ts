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
import { workdayProvider } from '../ats/providers/workday'
import { jobviteProvider } from '../ats/providers/jobvite'
import { bamboohrProvider } from '../ats/providers/bamboohr'
import { icimsProvider } from '../ats/providers/icims'
import { oracleProvider } from '../ats/providers/oracle'
import { successfactorsProvider } from '../ats/providers/successfactors'

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
  workdayProvider,
  jobviteProvider,
  bamboohrProvider,
  icimsProvider,
  oracleProvider,
  successfactorsProvider,
]

const dynamicProviders = new Map<ProviderId, JobProvider>()

function applyConfigs(providers: JobProvider[], configs: ProviderConfig[]): JobProvider[] {
  return providers.map(dp => {
    const config = configs.find(c => c.id === dp.id)
    if (config) {
      return { ...dp, enabled: config.enabled, priority: config.priority }
    }
    return dp
  })
}

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
    const staticProviders = applyConfigs(DEFAULT_PROVIDERS, configs)
    const dynamicProviderList: JobProvider[] = []
    for (const [id, provider] of dynamicProviders) {
      const config = configs.find(c => c.id === id)
      if (config) {
        dynamicProviderList.push({ ...provider, enabled: config.enabled, priority: config.priority })
      } else {
        dynamicProviderList.push(provider)
      }
    }
    return [...staticProviders, ...dynamicProviderList]
  },

  get(id: ProviderId): JobProvider | undefined {
    return this.getAll().find(p => p.id === id)
  },

  getEnabled(): JobProvider[] {
    return this.getAll().filter(p => p.enabled)
  },

  register(provider: JobProvider): void {
    dynamicProviders.set(provider.id, provider)
    const configs = get<ProviderConfig[]>('provider_configs', [])
    if (!configs.find(c => c.id === provider.id)) {
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
    }
  },

  remove(id: ProviderId): void {
    dynamicProviders.delete(id)
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
