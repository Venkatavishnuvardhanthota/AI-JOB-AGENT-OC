import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { savedFilterStorage, type SavedFilter } from '@/services/storage'
import { Bookmark, BookmarkCheck, Save, Plus, Pencil, Trash2, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { FilterValues } from './application-filters'

interface SavedFiltersProps {
  currentFilters: FilterValues
  onApply: (filters: FilterValues) => void
}

export function SavedFilters({ currentFilters, onApply }: SavedFiltersProps) {
  const [filters, setFilters] = useState<SavedFilter[]>([])
  const [showSave, setShowSave] = useState(false)
  const [filterName, setFilterName] = useState('')
  const [renaming, setRenaming] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')

  useEffect(() => { setFilters(savedFilterStorage.list()) }, [])

  const refresh = () => setFilters(savedFilterStorage.list())

  const hasFilterValues = currentFilters.search || currentFilters.status || currentFilters.priority ||
    currentFilters.company || currentFilters.location || currentFilters.recruiter ||
    currentFilters.date_from || currentFilters.date_to

  const handleSave = () => {
    if (!filterName.trim()) return
    savedFilterStorage.save({
      id: crypto.randomUUID(),
      name: filterName.trim(),
      search: currentFilters.search,
      status: currentFilters.status,
      priority: currentFilters.priority,
      company: currentFilters.company,
      location: currentFilters.location,
      recruiter: currentFilters.recruiter,
      date_from: currentFilters.date_from,
      date_to: currentFilters.date_to,
      sort_by: '',
      sort_order: '',
      is_default: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
    setFilterName('')
    setShowSave(false)
    refresh()
  }

  const handleApply = (f: SavedFilter) => {
    onApply({
      search: f.search, status: f.status, priority: f.priority,
      company: f.company, location: f.location, recruiter: f.recruiter,
      date_from: f.date_from, date_to: f.date_to,
    })
  }

  const handleRename = (id: string) => {
    if (renameValue.trim()) savedFilterStorage.rename(id, renameValue.trim())
    setRenaming(null)
    setRenameValue('')
    refresh()
  }

  const defaultFilter = filters.find(f => f.is_default)

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 flex-wrap">
        {filters.map(f => (
          <div key={f.id} className="group relative">
            {renaming === f.id ? (
              <div className="flex items-center gap-1">
                <Input
                  value={renameValue}
                  onChange={(e) => setRenameValue(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') handleRename(f.id); if (e.key === 'Escape') setRenaming(null) }}
                  className="h-7 text-xs w-36"
                  autoFocus
                />
                <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => handleRename(f.id)}><X className="h-3 w-3" /></Button>
              </div>
            ) : (
              <button
                onClick={() => handleApply(f)}
                className={cn(
                  "flex items-center gap-1 rounded-md px-2 py-1 text-xs transition-colors border",
                  f.is_default
                    ? "bg-primary/10 border-primary/30 text-primary"
                    : "bg-dark-800 border-glass-border text-muted-foreground hover:text-foreground hover:border-primary/30"
                )}
                title={f.name}
              >
                {f.is_default ? <BookmarkCheck className="h-3 w-3" /> : <Bookmark className="h-3 w-3" />}
                <span className="max-w-24 truncate">{f.name}</span>
                <button
                  onClick={(e) => { e.stopPropagation(); setRenaming(f.id); setRenameValue(f.name) }}
                  className="ml-1 opacity-0 group-hover:opacity-100 transition-opacity"
                  aria-label={`Rename ${f.name}`}
                >
                  <Pencil className="h-2.5 w-2.5" />
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); if (confirm(`Delete "${f.name}"?`)) { savedFilterStorage.delete(f.id); refresh() } }}
                  className="opacity-0 group-hover:opacity-100 transition-opacity"
                  aria-label={`Delete ${f.name}`}
                >
                  <Trash2 className="h-2.5 w-2.5 text-error" />
                </button>
              </button>
            )}
          </div>
        ))}
        {hasFilterValues && (
          <>
            {showSave ? (
              <div className="flex items-center gap-1">
                <Input
                  value={filterName}
                  onChange={(e) => setFilterName(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') handleSave(); if (e.key === 'Escape') setShowSave(false) }}
                  placeholder="Filter name..."
                  className="h-7 text-xs w-32"
                  autoFocus
                />
                <Button variant="ghost" size="icon" className="h-6 w-6" onClick={handleSave} disabled={!filterName.trim()}>
                  <Save className="h-3 w-3" />
                </Button>
                <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setShowSave(false)}>
                  <X className="h-3 w-3" />
                </Button>
              </div>
            ) : (
              <Button variant="outline" size="sm" className="h-7 text-xs" onClick={() => setShowSave(true)}>
                <Plus className="h-3 w-3 mr-1" /> Save Filter
              </Button>
            )}
          </>
        )}
      </div>
      {defaultFilter && (
        <p className="text-[10px] text-muted-foreground">Default: {defaultFilter.name}</p>
      )}
    </div>
  )
}
