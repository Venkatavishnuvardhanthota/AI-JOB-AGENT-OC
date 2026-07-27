const PREFIX = 'ajapp_'

function get<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(PREFIX + key)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function set<T>(key: string, value: T): void {
  try {
    localStorage.setItem(PREFIX + key, JSON.stringify(value))
  } catch { /* quota exceeded, silently fail */ }
}

function remove(key: string): void {
  localStorage.removeItem(PREFIX + key)
}

export interface SavedFilter {
  id: string
  name: string
  search: string
  status: string
  priority: string
  company: string
  location: string
  recruiter: string
  date_from: string
  date_to: string
  sort_by: string
  sort_order: string
  is_default: boolean
  created_at: string
  updated_at: string
}

const FILTERS_KEY = 'saved_filters'
const DEFAULT_KEY = 'default_filter_id'
const RECENT_KEY = 'recent_searches'
const MAX_RECENT = 10

export const savedFilterStorage = {
  list(): SavedFilter[] {
    return get<SavedFilter[]>(FILTERS_KEY) || []
  },

  save(filter: SavedFilter): void {
    const filters = this.list()
    const idx = filters.findIndex(f => f.id === filter.id)
    if (idx >= 0) filters[idx] = { ...filter, updated_at: new Date().toISOString() }
    else filters.push(filter)
    set(FILTERS_KEY, filters)
  },

  delete(id: string): void {
    set(FILTERS_KEY, this.list().filter(f => f.id !== id))
    const defId = get<string>(DEFAULT_KEY)
    if (defId === id) remove(DEFAULT_KEY)
  },

  getDefault(): SavedFilter | null {
    const id = get<string>(DEFAULT_KEY)
    if (!id) return null
    return this.list().find(f => f.id === id) || null
  },

  setDefault(id: string): void {
    set(DEFAULT_KEY, id)
  },

  clearDefault(): void {
    remove(DEFAULT_KEY)
  },

  rename(id: string, name: string): void {
    const filters = this.list()
    const f = filters.find(f => f.id === id)
    if (f) { f.name = name; f.updated_at = new Date().toISOString() }
    set(FILTERS_KEY, filters)
  },
}

export interface RecentSearch {
  id: string
  query: string
  filters: { search: string; status: string; priority: string; company: string; location: string; recruiter: string; date_from: string; date_to: string }
  pinned: boolean
  created_at: string
}

export const recentSearchStorage = {
  list(): RecentSearch[] {
    return get<RecentSearch[]>(RECENT_KEY) || []
  },

  add(search: Omit<RecentSearch, 'id' | 'pinned' | 'created_at'>): void {
    const searches = this.list().filter(s => s.query !== search.query || JSON.stringify(s.filters) !== JSON.stringify(search.filters))
    searches.unshift({ ...search, id: crypto.randomUUID(), pinned: false, created_at: new Date().toISOString() })
    if (searches.length > MAX_RECENT) searches.pop()
    set(RECENT_KEY, searches)
  },

  togglePin(id: string): void {
    const searches = this.list()
    const s = searches.find(s => s.id === id)
    if (s) s.pinned = !s.pinned
    searches.sort((a, b) => (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0))
    set(RECENT_KEY, searches)
  },

  remove(id: string): void {
    set(RECENT_KEY, this.list().filter(s => s.id !== id))
  },

  clear(): void {
    remove(RECENT_KEY)
  },
}
