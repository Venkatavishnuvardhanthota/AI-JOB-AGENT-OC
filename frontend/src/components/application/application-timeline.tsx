import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { timelineService } from '@/services/timeline'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/layout/empty-state'
import { Clock, Search, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ApplicationTimelineProps {
  applicationId: string
}

const FILTER_OPTIONS = [
  { value: '', label: 'All Events' },
  { value: 'status_change', label: 'Status Changes' },
  { value: 'note', label: 'Notes' },
  { value: 'document', label: 'Documents' },
  { value: 'interview', label: 'Interviews' },
  { value: 'recruiter', label: 'Recruiter Activity' },
  { value: 'system', label: 'System Events' },
] as const

export function ApplicationTimeline({ applicationId }: ApplicationTimelineProps) {
  const [filterType, setFilterType] = useState('')
  const [search, setSearch] = useState('')

  const { data: entries, isLoading } = useQuery({
    queryKey: ['applications', applicationId, 'timeline'],
    queryFn: () => timelineService.list(applicationId),
    enabled: !!applicationId,
  })

  const filtered = useMemo(() => {
    if (!entries) return []
    return entries.filter(e => {
      if (filterType && !e.event_type.includes(filterType)) return false
      if (search && !e.description.toLowerCase().includes(search.toLowerCase())) return false
      return true
    })
  }, [entries, filterType, search])

  const hasFilters = filterType || search

  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle>Timeline</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </CardContent>
      </Card>
    )
  }

  if (!entries?.length) {
    return (
      <Card>
        <CardHeader><CardTitle>Timeline</CardTitle></CardHeader>
        <CardContent>
          <EmptyState icon={Clock} title="No timeline entries" description="Events will appear here as the application progresses." />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Timeline</CardTitle>
        <div className="flex items-center gap-2 mt-2">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search timeline..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8 h-8 text-xs"
              aria-label="Search timeline entries"
            />
          </div>
          <Select value={filterType} onChange={(e) => setFilterType(e.target.value)} className="w-36 h-8 text-xs" aria-label="Filter timeline by type">
            {FILTER_OPTIONS.map(o => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </Select>
          {hasFilters && (
            <Button variant="ghost" size="sm" className="h-8 text-xs" onClick={() => { setFilterType(''); setSearch('') }}>
              <X className="h-3 w-3 mr-1" /> Clear
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {filtered.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">No entries match your filters.</p>
        ) : (
          <div className="relative space-y-0" role="list" aria-label="Application timeline">
            {filtered.map((entry, index) => (
              <div key={entry.id} className="flex gap-4 pb-6 relative" role="listitem">
                <div className="flex flex-col items-center">
                  <div className={cn(
                    "h-3 w-3 rounded-full border-2 z-10",
                    index === 0 ? "bg-primary border-primary" : "bg-dark-800 border-muted-foreground/30"
                  )} />
                  {index < filtered.length - 1 && (
                    <div className="w-px flex-1 bg-glass-border mt-1" />
                  )}
                </div>
                <div className="flex-1 pt-0.5">
                  <p className="text-sm font-medium">{entry.description}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {new Date(entry.created_at).toLocaleString()}
                  </p>
                  {entry.metadata && Object.keys(entry.metadata).length > 0 && (
                    <p className="text-xs text-muted-foreground mt-1 italic">
                      {JSON.stringify(entry.metadata)}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
