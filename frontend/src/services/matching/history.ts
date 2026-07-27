import type { MatchHistoryEntry } from './types'

const PREFIX = 'ajapp_match_hist_'

function get<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch { return fallback }
}

function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

export const matchHistoryService = {
  getAll(): MatchHistoryEntry[] {
    return get<MatchHistoryEntry[]>(`${PREFIX}entries`, [])
  },

  add(entry: MatchHistoryEntry): void {
    const entries = this.getAll()
    entries.unshift(entry)
    set(`${PREFIX}entries`, entries.slice(0, 200))
  },

  getRecent(limit: number = 20): MatchHistoryEntry[] {
    return this.getAll().slice(0, limit)
  },

  getByJob(jobId: string): MatchHistoryEntry | undefined {
    return this.getAll().find(e => e.jobId === jobId)
  },

  clear(): void {
    set(`${PREFIX}entries`, [])
  },
}
