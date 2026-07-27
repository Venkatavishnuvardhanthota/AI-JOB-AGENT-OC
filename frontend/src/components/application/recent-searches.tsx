import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { recentSearchStorage, type RecentSearch } from '@/services/storage'
import { History, Pin, PinOff, X, Trash2, Search } from 'lucide-react'
import type { FilterValues } from './application-filters'

interface RecentSearchesProps {
  onApply: (filters: FilterValues) => void
  currentFilters: FilterValues
}

export function RecentSearches({ onApply, currentFilters }: RecentSearchesProps) {
  const [searches, setSearches] = useState<RecentSearch[]>([])

  useEffect(() => { setSearches(recentSearchStorage.list()) }, [])

  const refresh = () => setSearches(recentSearchStorage.list())

  const hasFilters = currentFilters.search || currentFilters.status || currentFilters.priority ||
    currentFilters.company || currentFilters.location

  const handleApply = (s: RecentSearch) => {
    onApply(s.filters)
  }

  if (searches.length === 0 && !hasFilters) return null

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {hasFilters && (
        <Button
          variant="ghost"
          size="sm"
          className="h-7 text-xs"
          onClick={() => {
            recentSearchStorage.add({ query: currentFilters.search || 'Custom search', filters: currentFilters })
            refresh()
          }}
        >
          <Search className="h-3 w-3 mr-1" /> Save Search
        </Button>
      )}
      {searches.slice(0, 10).map(s => (
        <button
          key={s.id}
          onClick={() => handleApply(s)}
          className="flex items-center gap-1 rounded-md px-2 py-1 text-xs bg-dark-800 border border-glass-border text-muted-foreground hover:text-foreground hover:border-primary/30 transition-colors"
          title={s.query}
        >
          {s.pinned ? <Pin className="h-3 w-3" /> : <History className="h-3 w-3" />}
          <span className="max-w-24 truncate">{s.query || 'Search'}</span>
          <button
            onClick={(e) => { e.stopPropagation(); recentSearchStorage.togglePin(s.id); refresh() }}
            className="ml-1 hover:text-primary"
            aria-label={s.pinned ? 'Unpin' : 'Pin'}
          >
            {s.pinned ? <PinOff className="h-2.5 w-2.5" /> : <Pin className="h-2.5 w-2.5" />}
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); recentSearchStorage.remove(s.id); refresh() }}
            className="hover:text-error"
            aria-label="Remove"
          >
            <X className="h-2.5 w-2.5" />
          </button>
        </button>
      ))}
      {searches.length > 0 && (
        <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={() => { if (confirm('Clear all recent searches?')) { recentSearchStorage.clear(); refresh() } }}>
          <Trash2 className="h-3 w-3 mr-1" /> Clear
        </Button>
      )}
    </div>
  )
}
