import { useState, useMemo, useCallback, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { applicationService } from '@/services/application'
import { PageHeader } from '@/components/layout/page-header'
import { DataTable, type Column } from '@/components/layout/data-table'
import { EmptyState } from '@/components/layout/empty-state'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  ApplicationStatusBadge,
  ApplicationPriorityBadge,
  ApplicationFilters,
  ApplicationStatsCards,
  BulkActions,
  QuickActionsDropdown,
} from '@/components/application'
import { ApplicationCard } from '@/components/application/application-card'
import type { FilterValues } from '@/components/application'
import type { Application, ApplicationSearchParams } from '@/types'
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts'
import { getApplicationAge } from '@/hooks/useApplicationAge'
import { getReminderBadges } from '@/hooks/useReminderBadges'
import { FileText, Building2, MapPin, ExternalLink, Plus, SlidersHorizontal } from 'lucide-react'
import { cn } from '@/lib/utils'



const DEFAULT_FILTERS: FilterValues = {
  search: '', status: '', priority: '', company: '', location: '',
  recruiter: '', date_from: '', date_to: '',
}

export function ApplicationsPage() {
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState<FilterValues>(DEFAULT_FILTERS)
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [showFilters, setShowFilters] = useState(false)
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table')
  const searchRef = useRef<HTMLInputElement>(null)

  const searchParams = useMemo<ApplicationSearchParams>(() => {
    const params: ApplicationSearchParams = { page, page_size: 20 }
    if (filters.search) params.search = filters.search
    if (filters.status) params.status = filters.status as any
    if (filters.priority) params.priority = filters.priority as any
    if (filters.company) params.company = filters.company
    if (filters.location) params.location = filters.location
    if (filters.recruiter) params.recruiter = filters.recruiter
    if (filters.date_from) params.date_from = filters.date_from
    if (filters.date_to) params.date_to = filters.date_to
    return params
  }, [page, filters])

  const { data, isLoading } = useQuery({
    queryKey: ['applications', searchParams],
    queryFn: () => applicationService.list(searchParams),
  })

  const items: Application[] = data?.items || []

  useKeyboardShortcuts([
    { key: '/', handler: () => searchRef.current?.focus() },
    { key: 'f', handler: () => setShowFilters(v => !v) },
    { key: 'Escape', handler: () => { setSelectedIds([]); setFilters(DEFAULT_FILTERS); setPage(1) }, ignoreWhenFocused: false },
    {
      key: 'a', ctrl: true,
      handler: () => setSelectedIds(prev => prev.length === items.length ? [] : items.map(i => i.id)),
    },
  ])

  const handleFilterChange = useCallback((values: FilterValues) => {
    setFilters(values)
    setPage(1)
    setSelectedIds([])
  }, [])

  const handleReset = useCallback(() => {
    setFilters(DEFAULT_FILTERS)
    setPage(1)
    setSelectedIds([])
  }, [])

  const toggleSelect = useCallback((id: string) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id])
  }, [])

  const toggleSelectAll = useCallback(() => {
    if (selectedIds.length === items.length) {
      setSelectedIds([])
    } else {
      setSelectedIds(items.map(i => i.id))
    }
  }, [items, selectedIds.length])

  const getAgeCell = (dateStr: string) => {
    const age = getApplicationAge(dateStr)
    return (
      <span className={cn("text-xs", age.isStale ? "text-warning" : "text-muted-foreground")} title={age.staleReason}>
        {age.label}
      </span>
    )
  }

  const getReminderCell = (app: Application) => {
    const badges = getReminderBadges(app)
    if (badges.length === 0) return null
    return (
      <div className="flex gap-1">
        {badges.slice(0, 2).map(b => (
          <Badge key={b.type} variant={b.variant} className="text-[10px] px-1 py-0">
            {b.label}
          </Badge>
        ))}
      </div>
    )
  }

  const columns: Column<Application>[] = [
    {
      key: 'select', header: '',
      className: 'w-10',
      cell: (app) => (
        <input
          type="checkbox"
          checked={selectedIds.includes(app.id)}
          onChange={() => toggleSelect(app.id)}
          className="h-4 w-4 rounded border-glass-border"
          aria-label={`Select ${app.job_title}`}
        />
      ),
    },
    {
      key: 'job', header: 'Job',
      cell: (app) => (
        <div>
          <Link to={`/applications/${app.id}`} className="text-sm font-medium hover:text-primary transition-colors">
            {app.job_title || app.job_id}
          </Link>
          <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
            <Building2 className="h-3 w-3" />
            {app.company_name}
          </p>
          {getReminderCell(app)}
        </div>
      ),
    },
    {
      key: 'status', header: 'Status',
      cell: (app) => <ApplicationStatusBadge status={app.status} />,
    },
    {
      key: 'priority', header: 'Priority',
      cell: (app) => <ApplicationPriorityBadge priority={app.priority} />,
    },
    {
      key: 'location', header: 'Location',
      cell: (app) => app.location ? (
        <span className="text-sm text-muted-foreground flex items-center gap-1">
          <MapPin className="h-3 w-3" />
          {app.location}
        </span>
      ) : <span className="text-sm text-muted-foreground">-</span>,
    },
    {
      key: 'age', header: 'Age',
      cell: (app) => getAgeCell(app.created_at),
    },
    {
      key: 'actions', header: '', className: 'text-right w-24',
      cell: (app) => (
        <div className="flex items-center justify-end gap-1">
          <Link to={`/applications/${app.id}`}>
            <Button variant="ghost" size="icon" className="h-8 w-8" aria-label={`View ${app.job_title}`}>
              <ExternalLink className="h-4 w-4" />
            </Button>
          </Link>
          <QuickActionsDropdown application={app} />
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Applications"
        description="Track and manage your job applications."
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant={showFilters ? 'default' : 'outline'}
              size="sm"
              onClick={() => setShowFilters(v => !v)}
              aria-label="Toggle filters"
            >
              <SlidersHorizontal className="h-4 w-4 mr-1" /> Filters
              <kbd className="ml-1.5 text-[10px] opacity-60">F</kbd>
            </Button>
            <Button variant="outline" size="sm" onClick={() => setViewMode(v => v === 'table' ? 'cards' : 'table')}>
              {viewMode === 'table' ? 'Cards' : 'Table'}
            </Button>
            <Link to="/jobs/search">
              <Button size="sm">
                <Plus className="h-4 w-4 mr-1" /> New
                <kbd className="ml-1.5 text-[10px] opacity-60">N</kbd>
              </Button>
            </Link>
          </div>
        }
      />

      <ApplicationStatsCards />

      {showFilters && (
        <div className="animate-in slide-in-from-top-2 duration-200">
          <ApplicationFilters values={filters} onChange={handleFilterChange} onReset={handleReset} />
        </div>
      )}

      {selectedIds.length > 0 && (
        <BulkActions selectedIds={selectedIds} onClear={() => setSelectedIds([])} />
      )}

      {!isLoading && items.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No applications yet"
          description="Start by creating an application for a job you're interested in."
          action={<Link to="/jobs/search"><Button>Browse Jobs</Button></Link>}
        />
      ) : (
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <input
                type="checkbox"
                checked={items.length > 0 && selectedIds.length === items.length}
                onChange={toggleSelectAll}
                className="h-4 w-4 rounded border-glass-border"
                aria-label="Select all"
              />
              Select all
              <kbd className="text-[10px] opacity-40 ml-1">Ctrl+A</kbd>
            </label>
            <p className="text-xs text-muted-foreground">
              {data?.total || 0} total
            </p>
          </div>

          {viewMode === 'cards' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {items.map(app => (
                <div key={app.id} className="relative">
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(app.id)}
                    onChange={() => toggleSelect(app.id)}
                    className="absolute top-2 left-2 z-10 h-4 w-4 rounded border-glass-border"
                    aria-label={`Select ${app.job_title}`}
                  />
                  <ApplicationCard application={app} />
                </div>
              ))}
            </div>
          ) : (
            <DataTable
              columns={columns}
              data={items}
              loading={isLoading}
              page={data?.page || page}
              totalPages={data?.total_pages || 1}
              total={data?.total}
              onPageChange={setPage}
            />
          )}
        </div>
      )}

      <div className="fixed bottom-4 right-4 z-30 hidden md:flex items-center gap-2 rounded-lg bg-dark-800 border border-glass-border px-3 py-2 shadow-lg">
        <span className="text-[10px] text-muted-foreground">
          <kbd className="px-1 py-0.5 rounded bg-dark-700 text-[10px]">/</kbd> Search
          <kbd className="ml-2 px-1 py-0.5 rounded bg-dark-700 text-[10px]">N</kbd> New
          <kbd className="ml-2 px-1 py-0.5 rounded bg-dark-700 text-[10px]">F</kbd> Filters
          <kbd className="ml-2 px-1 py-0.5 rounded bg-dark-700 text-[10px]">Esc</kbd> Clear
        </span>
      </div>
    </div>
  )
}
