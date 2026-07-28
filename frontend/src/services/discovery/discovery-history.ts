import type { DiscoveryHistoryEntry, DiscoveryStatistics } from './types'

const PREFIX = 'ajapp_disc_hist_'

function get<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch { return fallback }
}

function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

export const discoveryHistoryService = {
  getAll(): DiscoveryHistoryEntry[] {
    return get<DiscoveryHistoryEntry[]>(`${PREFIX}entries`, [])
  },

  get(id: string): DiscoveryHistoryEntry | undefined {
    return this.getAll().find(e => e.id === id)
  },

  add(entry: DiscoveryHistoryEntry): void {
    const entries = this.getAll()
    entries.unshift(entry)
    set(`${PREFIX}entries`, entries.slice(0, 500))
  },

  clear(): void {
    set(`${PREFIX}entries`, [])
  },

  getRecent(limit: number = 10): DiscoveryHistoryEntry[] {
    return this.getAll().slice(0, limit)
  },

  getByProfile(profileId: string): DiscoveryHistoryEntry[] {
    return this.getAll().filter(e => e.profileId === profileId)
  },

  getStatistics(): DiscoveryStatistics {
    const entries = this.getAll()
    const today = new Date().toISOString().split('T')[0]
    const weekAgo = new Date(Date.now() - 7 * 86400000).toISOString()
    const monthAgo = new Date(Date.now() - 30 * 86400000).toISOString()

    const keywordCounts = new Map<string, number>()
    const companyCounts = new Map<string, number>()
    const locationCounts = new Map<string, number>()

    for (const entry of entries) {
      if (entry.query) {
        const keyword = entry.query.toLowerCase().trim()
        keywordCounts.set(keyword, (keywordCounts.get(keyword) || 0) + 1)
      }
    }

    return {
      totalSearches: entries.length,
      totalJobsDiscovered: entries.reduce((sum, e) => sum + e.jobsFound, 0),
      totalDuplicatesRemoved: entries.reduce((sum, e) => sum + e.duplicatesRemoved, 0),
      averageExecutionTime: entries.length > 0
        ? entries.reduce((sum, e) => sum + e.executionTime, 0) / entries.length
        : 0,
      searchesToday: entries.filter(e => e.timestamp.startsWith(today)).length,
      searchesThisWeek: entries.filter(e => e.timestamp >= weekAgo).length,
      searchesThisMonth: entries.filter(e => e.timestamp >= monthAgo).length,
      topKeywords: [...keywordCounts.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(([keyword, count]) => ({ keyword, count })),
      topCompanies: [...companyCounts.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(([company, count]) => ({ company, count })),
      topLocations: [...locationCounts.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(([location, count]) => ({ location, count })),
    }
  },
}
