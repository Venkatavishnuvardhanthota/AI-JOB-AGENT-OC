import type { AuthConfiguration, StorageType } from './types'
import { DEFAULT_AUTH_CONFIGURATION } from './types'
import { validationEngine } from './validation-engine'

const PREFIX = 'ajapp_auth_cfg_'

function get<T>(key: string, fallback: T): T {
  try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback } catch { return fallback }
}
function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

let config: AuthConfiguration = { ...DEFAULT_AUTH_CONFIGURATION }

export const authConfiguration = {
  get(): AuthConfiguration {
    return { ...config }
  },

  update(updates: Partial<AuthConfiguration>): void {
    const validated = validationEngine.validateConfiguration(updates)
    if (!validated.valid) {
      throw new Error(`Invalid configuration: ${validated.errors.map(e => e.message).join(', ')}`)
    }
    config = { ...config, ...updates }
    set(PREFIX + 'settings', config)
  },

  setStorageType(type: StorageType): void {
    this.update({ storageType: type })
  },

  setSessionTimeout(ms: number): void {
    this.update({ sessionTimeoutMs: ms })
  },

  setRefreshEnabled(enabled: boolean): void {
    this.update({ refreshEnabled: enabled })
  },

  setMaxConcurrentSessions(count: number): void {
    this.update({ maxConcurrentSessions: count })
  },

  reset(): void {
    config = { ...DEFAULT_AUTH_CONFIGURATION }
    localStorage.removeItem(PREFIX + 'settings')
  },

  load(): void {
    const saved = get<AuthConfiguration | null>(PREFIX + 'settings', null)
    if (saved) config = { ...DEFAULT_AUTH_CONFIGURATION, ...saved }
  },
}
