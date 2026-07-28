import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Search, X } from 'lucide-react'
import type { ProviderFilterOptions, ProviderCategory } from '@/services/provider-management'

interface ProviderFiltersProps {
  filters: ProviderFilterOptions
  categories: ProviderCategory[]
  onFiltersChange: (filters: ProviderFilterOptions) => void
}

export function ProviderFilters({ filters, categories, onFiltersChange }: ProviderFiltersProps) {
  const update = (updates: Partial<ProviderFilterOptions>) => {
    onFiltersChange({ ...filters, ...updates })
  }

  const toggleCategory = (cat: string) => {
    const current = filters.categories
    update({ categories: current.includes(cat) ? current.filter(c => c !== cat) : [...current, cat] })
  }

  return (
    <div className="space-y-3">
      <div className="relative">
        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search providers..."
          className="pl-8 h-9 text-sm"
          value={filters.search}
          onChange={(e) => update({ search: e.target.value })}
        />
      </div>

      <div className="flex flex-wrap gap-1.5">
        {categories.map(cat => (
          <Badge
            key={cat.name}
            variant={filters.categories.includes(cat.name) ? 'default' : 'outline'}
            className="cursor-pointer text-[10px]"
            onClick={() => toggleCategory(cat.name)}
          >
            {cat.name}
            {filters.categories.includes(cat.name) && (
              <X className="h-2.5 w-2.5 ml-1" onClick={(e) => { e.stopPropagation(); toggleCategory(cat.name) }} />
            )}
          </Badge>
        ))}
      </div>

      <div className="flex gap-2">
        <select
          className="h-8 text-xs rounded-md border border-glass-border bg-dark-900 px-2 text-foreground"
          value={filters.sortBy}
          onChange={(e) => update({ sortBy: e.target.value as ProviderFilterOptions['sortBy'] })}
        >
          <option value="name">Name</option>
          <option value="priority">Priority</option>
          <option value="latency">Latency</option>
          <option value="reliability">Reliability</option>
          <option value="health">Health</option>
        </select>

        <select
          className="h-8 text-xs rounded-md border border-glass-border bg-dark-900 px-2 text-foreground"
          value={filters.sortOrder}
          onChange={(e) => update({ sortOrder: e.target.value as 'asc' | 'desc' })}
        >
          <option value="asc">Ascending</option>
          <option value="desc">Descending</option>
        </select>

        <select
          className="h-8 text-xs rounded-md border border-glass-border bg-dark-900 px-2 text-foreground"
          value={filters.enabled === null ? 'all' : filters.enabled ? 'enabled' : 'disabled'}
          onChange={(e) => {
            const v = e.target.value
            update({ enabled: v === 'all' ? null : v === 'enabled' })
          }}
        >
          <option value="all">All</option>
          <option value="enabled">Enabled</option>
          <option value="disabled">Disabled</option>
        </select>
      </div>
    </div>
  )
}
