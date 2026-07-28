import type { SearchProfile, ScheduleFrequency } from './types'

const PREFIX = 'ajapp_disc_profiles_'

function get<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch { return fallback }
}

function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

export const searchProfileService = {
  getAll(): SearchProfile[] {
    return get<SearchProfile[]>(PREFIX, [])
  },

  get(id: string): SearchProfile | undefined {
    return this.getAll().find(p => p.id === id)
  },

  create(profile: Omit<SearchProfile, 'id' | 'createdAt' | 'updatedAt' | 'lastRunAt'>): SearchProfile {
    const profiles = this.getAll()
    const now = new Date().toISOString()
    const newProfile: SearchProfile = {
      ...profile,
      id: `sp_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      createdAt: now,
      updatedAt: now,
      lastRunAt: null,
    }
    profiles.push(newProfile)
    set(PREFIX, profiles)
    return newProfile
  },

  update(id: string, updates: Partial<Omit<SearchProfile, 'id' | 'createdAt'>>): SearchProfile | undefined {
    const profiles = this.getAll()
    const idx = profiles.findIndex(p => p.id === id)
    if (idx === -1) return undefined
    profiles[idx] = { ...profiles[idx], ...updates, updatedAt: new Date().toISOString() }
    set(PREFIX, profiles)
    return profiles[idx]
  },

  remove(id: string): void {
    set(PREFIX, this.getAll().filter(p => p.id !== id))
  },

  markRun(id: string): void {
    this.update(id, { lastRunAt: new Date().toISOString() })
  },

  getByFrequency(frequency: ScheduleFrequency): SearchProfile[] {
    return this.getAll().filter(p => p.scheduleFrequency === frequency)
  },

  getDueProfiles(): SearchProfile[] {
    const now = Date.now()
    return this.getAll().filter(p => {
      if (p.scheduleFrequency === 'manual' || !p.lastRunAt) return false
      const lastRun = new Date(p.lastRunAt).getTime()
      const intervals: Record<ScheduleFrequency, number> = {
        manual: 0,
        hourly: 3600000,
        daily: 86400000,
        weekly: 604800000,
        monthly: 2592000000,
        custom_cron: 0,
      }
      return (now - lastRun) >= intervals[p.scheduleFrequency]
    })
  },
}
