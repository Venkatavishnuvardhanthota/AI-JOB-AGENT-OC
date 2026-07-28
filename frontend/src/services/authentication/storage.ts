import type { StorageType } from './types'
import { secureStorage } from '../production/security-service'

export interface CredentialStorage {
  readonly type: StorageType
  save(key: string, value: unknown): void
  load(key: string): unknown | null
  remove(key: string): void
  clear(): void
}

class MemoryStorage implements CredentialStorage {
  readonly type: StorageType = 'memory'
  private store = new Map<string, unknown>()

  save(key: string, value: unknown): void { this.store.set(key, value) }
  load(key: string): unknown | null { return this.store.get(key) ?? null }
  remove(key: string): void { this.store.delete(key) }
  clear(): void { this.store.clear() }
}

class EncryptedStorage implements CredentialStorage {
  readonly type: StorageType = 'encrypted'

  save(key: string, value: unknown): void {
    try {
      secureStorage.set(key, typeof value === 'string' ? value : JSON.stringify(value))
    } catch { }
  }

  load(key: string): unknown | null {
    try {
      const raw = secureStorage.get(key)
      if (!raw) return null
      try { return JSON.parse(raw) } catch { return raw }
    } catch { return null }
  }

  remove(key: string): void { secureStorage.remove(key) }
  clear(): void { }
}

class EnvironmentStorage implements CredentialStorage {
  readonly type: StorageType = 'environment'
  private store = new Map<string, unknown>()

  save(key: string, value: unknown): void { this.store.set(key, value) }
  load(key: string): unknown | null { return this.store.get(key) ?? null }
  remove(key: string): void { this.store.delete(key) }
  clear(): void { this.store.clear() }
}

const STORAGE_MAP: Record<StorageType, () => CredentialStorage> = {
  memory: () => new MemoryStorage(),
  encrypted: () => new EncryptedStorage(),
  environment: () => new EnvironmentStorage(),
  browser: () => new EncryptedStorage(),
  secret_manager: () => new EnvironmentStorage(),
}

let activeStorage: CredentialStorage = new MemoryStorage()

export const credentialStorage = {
  configure(type: StorageType): void {
    const factory = STORAGE_MAP[type]
    if (factory) activeStorage = factory()
  },

  get active(): CredentialStorage { return activeStorage },

  save(key: string, value: unknown): void { activeStorage.save(key, value) },
  load(key: string): unknown | null { return activeStorage.load(key) },
  remove(key: string): void { activeStorage.remove(key) },
  clear(): void { activeStorage.clear() },
}
