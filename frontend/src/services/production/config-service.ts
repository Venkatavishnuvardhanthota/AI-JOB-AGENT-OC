import type { ConfigOption } from './production-types'

const PREFIX = 'ajapp_cfg_'

function get<T>(key: string, fallback: T): T {
  try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback } catch { return fallback }
}
function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

export interface AppConfig {
  environment: 'development' | 'staging' | 'production'
  version: string
  features: Record<string, boolean>
  thresholds: {
    matchThreshold: number
    confidenceThreshold: number
    maxRetries: number
    maxConcurrency: number
    retryBaseDelay: number
    retryMaxDelay: number
    backoffFactor: number
    queueWarningDepth: number
    queueCriticalDepth: number
    alertErrorRateThreshold: number
    slowResponseThreshold: number
  }
  providers: Record<string, boolean>
  maintenance: {
    logRetentionDays: number
    metricRetentionDays: number
    alertRetentionDays: number
    historyPruningDays: number
  }
}

const DEFAULT_CONFIG: AppConfig = {
  environment: 'development',
  version: '2.1.0',
  features: {
    orchestration: true,
    browserAutomation: true,
    autoApplicationGeneration: true,
    analytics: true,
    notifications: true,
    darkMode: true,
  },
  thresholds: {
    matchThreshold: 0.7,
    confidenceThreshold: 60,
    maxRetries: 3,
    maxConcurrency: 5,
    retryBaseDelay: 1000,
    retryMaxDelay: 30000,
    backoffFactor: 2,
    queueWarningDepth: 50,
    queueCriticalDepth: 100,
    alertErrorRateThreshold: 10,
    slowResponseThreshold: 5000,
  },
  providers: {
    indeed: true,
    linkedin: true,
    glassdoor: true,
    ziprecruiter: true,
    monster: false,
  },
  maintenance: {
    logRetentionDays: 30,
    metricRetentionDays: 90,
    alertRetentionDays: 60,
    historyPruningDays: 180,
  },
}

export const configService = {
  get(): AppConfig {
    return get<AppConfig>(PREFIX + 'config', DEFAULT_CONFIG)
  },

  update(updates: Partial<AppConfig>): AppConfig {
    const config = this.get()
    const merged = { ...config, ...updates }
    set(PREFIX + 'config', merged)
    return merged
  },

  reset(): AppConfig {
    set(PREFIX + 'config', DEFAULT_CONFIG)
    return DEFAULT_CONFIG
  },

  getFeatureFlag(key: string): boolean {
    return this.get().features[key] ?? false
  },

  setFeatureFlag(key: string, enabled: boolean): void {
    const config = this.get()
    config.features[key] = enabled
    set(PREFIX + 'config', config)
  },

  isProviderEnabled(provider: string): boolean {
    return this.get().providers[provider] ?? false
  },

  toggleProvider(provider: string, enabled: boolean): void {
    const config = this.get()
    config.providers[provider] = enabled
    set(PREFIX + 'config', config)
  },

  getThreshold(key: keyof AppConfig['thresholds']): number {
    return this.get().thresholds[key]
  },

  updateThreshold(key: keyof AppConfig['thresholds'], value: number): void {
    const config = this.get()
    config.thresholds[key] = value
    set(PREFIX + 'config', config)
  },

  getEnvironment(): AppConfig['environment'] {
    return this.get().environment
  },

  getOptions(): ConfigOption[] {
    const config = this.get()
    const options: ConfigOption[] = []
    for (const [key, value] of Object.entries(config.features)) {
      options.push({ key: `features.${key}`, value, type: 'boolean', description: `Feature flag: ${key}`, environment: 'all', runtime: true, category: 'features' })
    }
    for (const [key, value] of Object.entries(config.thresholds)) {
      options.push({ key: `thresholds.${key}`, value, type: typeof value === 'number' ? 'number' : 'string', description: `Threshold: ${key}`, environment: 'all', runtime: true, category: 'thresholds' })
    }
    for (const [key, value] of Object.entries(config.providers)) {
      options.push({ key: `providers.${key}`, value, type: 'boolean', description: `Provider toggle: ${key}`, environment: 'all', runtime: true, category: 'providers' })
    }
    for (const [key, value] of Object.entries(config.maintenance)) {
      options.push({ key: `maintenance.${key}`, value, type: 'number', description: `Maintenance: ${key}`, environment: 'all', runtime: false, category: 'maintenance' })
    }
    options.push({ key: 'environment', value: config.environment, type: 'string', description: 'Deployment environment', environment: 'all', runtime: false, category: 'system' })
    return options
  },

  validate(): { valid: boolean; errors: string[]; warnings: string[] } {
    const config = this.get()
    const errors: string[] = []
    const warnings: string[] = []

    if (config.thresholds.matchThreshold < 0 || config.thresholds.matchThreshold > 1) {
      errors.push('matchThreshold must be between 0 and 1')
    }
    if (config.thresholds.maxRetries < 0) errors.push('maxRetries must be non-negative')
    if (config.thresholds.maxConcurrency < 1) errors.push('maxConcurrency must be at least 1')
    if (config.environment === 'production' && config.thresholds.maxConcurrency > 20) {
      warnings.push('maxConcurrency is high for production')
    }
    if (config.environment === 'production' && !config.features.orchestration) {
      warnings.push('Orchestration is disabled in production')
    }
    return { valid: errors.length === 0, errors, warnings }
  },
}
