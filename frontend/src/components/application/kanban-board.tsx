import { useState, useCallback, useMemo, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { applicationService } from '@/services/application'
import { APPLICATION_STATUSES, canTransition, getStatusLabel } from '@/services/status'
import { preferenceService } from '@/services/preferences'
import { KanbanColumn } from './kanban-column'
import { SwimlaneContainer } from './swimlane-container'
import { ColumnCustomizer } from './column-customizer'
import { QuickPreview } from './quick-preview'
import { KanbanCard } from './kanban-card'
import { ApplicationFilters } from './application-filters'
import { BulkActions } from './bulk-actions'
import { SavedFilters } from './saved-filters'
import { RecentSearches } from './recent-searches'
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts'
import { useToast } from '@/components/ui/toast'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import type { Application, ApplicationStatus } from '@/types'
import type { FilterValues } from './application-filters'
import type { GroupBy, ColumnRuleResult } from '@/services/pipeline'
import { GROUP_BY_OPTIONS } from '@/services/pipeline'
import { evaluateColumnRule, DEFAULT_COLUMN_RULES, getColumnValidation } from '@/services/pipeline'
import { SlidersHorizontal, Undo2, X, Plus } from 'lucide-react'
import { Link } from 'react-router-dom'

const DEFAULT_FILTERS: FilterValues = {
  search: '', status: '', priority: '', company: '', location: '',
  recruiter: '', date_from: '', date_to: '',
}

interface UndoState {
  applicationId: string
  fromStatus: ApplicationStatus
  toStatus: ApplicationStatus
}

export function KanbanBoard() {
  const queryClient = useQueryClient()
  const { addToast } = useToast()
  const [filters, setFilters] = useState<FilterValues>(DEFAULT_FILTERS)
  const [showFilters, setShowFilters] = useState(false)
  const [groupBy, setGroupBy] = useState<GroupBy>(preferenceService.getGroupBy())
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [previewApp, setPreviewApp] = useState<Application | null>(null)
  const [undo, setUndo] = useState<UndoState | null>(null)
  const boardRef = useRef<HTMLDivElement>(null)
  const searchRef = useRef<HTMLInputElement>(null)

  const [columnVisibility, setColumnVisibility] = useState<Record<string, boolean>>(() => preferenceService.getColumnVisibility())
  const [columnOrder, setColumnOrderState] = useState<ApplicationStatus[]>(() => {
    const saved = preferenceService.getColumnOrder()
    return saved.length > 0 ? saved : APPLICATION_STATUSES as unknown as ApplicationStatus[]
  })

  const searchParams = useMemo(() => {
    const params: Record<string, string> = { page_size: '500' }
    if (filters.search) params.search = filters.search
    if (filters.status) params.status = filters.status
    if (filters.priority) params.priority = filters.priority
    if (filters.company) params.company = filters.company
    if (filters.location) params.location = filters.location
    if (filters.recruiter) params.recruiter = filters.recruiter
    if (filters.date_from) params.date_from = filters.date_from
    if (filters.date_to) params.date_to = filters.date_to
    return params
  }, [filters])

  const { data, isLoading } = useQuery({
    queryKey: ['applications', 'kanban', searchParams],
    queryFn: () => applicationService.list(searchParams as any),
  })

  const items: Application[] = data?.items || []

  const moveMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: ApplicationStatus }) =>
      applicationService.updateStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })

  const columns = useMemo(() => {
    const statusItems = new Map<ApplicationStatus, Application[]>()
    for (const s of columnOrder) {
      statusItems.set(s, [])
    }
    for (const app of items) {
      const col = statusItems.get(app.status)
      if (col) col.push(app)
    }
    return columnOrder
      .filter(s => columnVisibility[s] !== false)
      .map(s => ({ status: s, applications: statusItems.get(s) || [] }))
  }, [items, columnOrder, columnVisibility])

  const globalRules = useMemo(() => {
    const results: ColumnRuleResult[] = []
    for (const col of columns) {
      const validation = getColumnValidation(col.applications, col.status)
      for (const rule of DEFAULT_COLUMN_RULES.filter(r => r.enabled)) {
        const result = evaluateColumnRule(rule, col.applications, validation)
        if (result) results.push(result)
      }
    }
    return results
  }, [columns])

  useKeyboardShortcuts([
    { key: '/', handler: () => searchRef.current?.focus() },
    { key: 'f', handler: () => setShowFilters(v => !v) },
    { key: 'Escape', handler: () => { setSelectedIds([]); setPreviewApp(null) }, ignoreWhenFocused: false },
    { key: 'z', ctrl: true, handler: () => undo && handleUndo() },
  ])

  const handleDrop = useCallback((applicationId: string, toStatus: ApplicationStatus) => {
    const app = items.find(a => a.id === applicationId)
    if (!app) return
    if (!canTransition(app.status, toStatus)) {
      addToast(`Cannot move "${app.job_title}" from "${getStatusLabel(app.status)}" to "${getStatusLabel(toStatus)}". Invalid transition.`, 'error')
      return
    }
    setUndo({ applicationId, fromStatus: app.status, toStatus })
    moveMutation.mutate({ id: applicationId, status: toStatus })
    addToast(`Moved "${app.job_title}" to ${getStatusLabel(toStatus)}`, 'success')
  }, [items, moveMutation, addToast])

  const handleUndo = useCallback(() => {
    if (!undo) return
    moveMutation.mutate({ id: undo.applicationId, status: undo.fromStatus })
    addToast('Move undone', 'info')
    setUndo(null)
  }, [undo, moveMutation, addToast])

  const handleSelect = useCallback((id: string, shiftKey: boolean) => {
    setSelectedIds(prev => {
      if (shiftKey && prev.length > 0) {
        const allIds = items.map(i => i.id)
        const lastIdx = allIds.indexOf(prev[prev.length - 1])
        const currIdx = allIds.indexOf(id)
        if (lastIdx !== -1 && currIdx !== -1) {
          const start = Math.min(lastIdx, currIdx)
          const end = Math.max(lastIdx, currIdx)
          const range = allIds.slice(start, end + 1)
          return [...new Set([...prev, ...range])]
        }
      }
      return prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    })
  }, [items])

  const handleReorderColumns = useCallback((newOrder: ApplicationStatus[]) => {
    setColumnOrderState(newOrder)
  }, [])

  const handleFilterChange = useCallback((values: FilterValues) => {
    setFilters(values)
    setSelectedIds([])
  }, [])

  const handleReset = useCallback(() => {
    setFilters(DEFAULT_FILTERS)
    setSelectedIds([])
  }, [])

  const handleGroupByChange = useCallback((value: GroupBy) => {
    setGroupBy(value)
    preferenceService.setGroupBy(value)
  }, [])

  const globalWarningCount = globalRules.filter(r => r.severity === 'warning' || r.severity === 'critical').length

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="h-8 w-48 bg-dark-700 rounded animate-pulse" />
            <div className="h-4 w-72 bg-dark-700 rounded animate-pulse" />
          </div>
        </div>
        <div className="flex gap-4 overflow-x-auto pb-4">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="min-w-[280px] h-[400px] bg-dark-800 rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Pipeline Board</h1>
          <p className="text-sm text-muted-foreground">
            {items.length} application{items.length !== 1 ? 's' : ''} across {columns.length} columns
            {globalWarningCount > 0 && (
              <span className="ml-2 text-warning">({globalWarningCount} rule{globalWarningCount > 1 ? 's' : ''} triggered)</span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <SavedFilters currentFilters={filters as any} onApply={handleFilterChange as any} />
          <Button variant={showFilters ? 'default' : 'outline'} size="sm" onClick={() => setShowFilters(v => !v)} aria-label="Toggle filters">
            <SlidersHorizontal className="h-4 w-4 mr-1" /> Filters
            <kbd className="ml-1.5 text-[10px] opacity-60">F</kbd>
          </Button>
          <Select
            value={groupBy}
            onChange={(e) => handleGroupByChange(e.target.value as GroupBy)}
            aria-label="Group by"
            className="w-32"
          >
            {GROUP_BY_OPTIONS.map(o => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </Select>
          <ColumnCustomizer
            statuses={columnOrder}
            visibility={columnVisibility}
            onVisibilityChange={setColumnVisibility}
            onReorder={handleReorderColumns}
          />
          <Link to="/jobs/search">
            <Button size="sm">
              <Plus className="h-4 w-4 mr-1" /> New
              <kbd className="ml-1.5 text-[10px] opacity-60">N</kbd>
            </Button>
          </Link>
        </div>
      </div>

      {showFilters && (
        <div className="animate-in slide-in-from-top-2 duration-200">
          <RecentSearches currentFilters={filters as any} onApply={handleFilterChange as any} />
          <ApplicationFilters values={filters} onChange={handleFilterChange} onReset={handleReset} />
        </div>
      )}

      {undo && (
        <div className="flex items-center gap-2 px-3 py-2 bg-primary/10 border border-primary/30 rounded-lg text-sm">
          <span>Moved to {getStatusLabel(undo.toStatus)}</span>
          <Button variant="outline" size="sm" onClick={handleUndo}>
            <Undo2 className="h-3 w-3 mr-1" /> Undo
            <kbd className="ml-1 text-[10px] opacity-60">Ctrl+Z</kbd>
          </Button>
          <button onClick={() => setUndo(null)} className="ml-auto p-0.5 hover:text-foreground">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {selectedIds.length > 0 && (
        <BulkActions selectedIds={selectedIds} onClear={() => setSelectedIds([])} />
      )}

      {groupBy === 'none' ? (
        <div
          ref={boardRef}
          className="flex gap-4 overflow-x-auto pb-6 -mx-4 px-4"
          style={{ minHeight: '60vh' }}
        >
          {columns.map(col => (
            <KanbanColumn
              key={col.status}
              status={col.status}
              applications={col.applications}
              onDrop={handleDrop}
              onPreview={setPreviewApp}
              selectedIds={selectedIds}
              onSelect={handleSelect}
            />
          ))}
          {columns.length === 0 && (
            <div className="flex items-center justify-center w-full text-muted-foreground">
              <p>No visible columns. Use the Columns menu to show columns.</p>
            </div>
          )}
        </div>
      ) : (
        <SwimlaneContainer
          applications={items}
          groupBy={groupBy}
          renderCard={(app) => (
            <div
              draggable
              onDragStart={(e) => {
                e.dataTransfer.setData('text/plain', app.id)
                e.dataTransfer.effectAllowed = 'move'
              }}
            >
              <KanbanCard
                application={app}
                onPreview={setPreviewApp}
                selected={selectedIds.includes(app.id)}
                onSelect={handleSelect}
              />
            </div>
          )}
        />
      )}

      {previewApp && (
        <QuickPreview application={previewApp} onClose={() => setPreviewApp(null)} />
      )}

      <div className="fixed bottom-4 right-4 z-30 hidden md:flex items-center gap-2 rounded-lg bg-dark-800 border border-glass-border px-3 py-2 shadow-lg">
        <span className="text-[10px] text-muted-foreground">
          <kbd className="px-1 py-0.5 rounded bg-dark-700 text-[10px]">/</kbd> Search
          <kbd className="ml-2 px-1 py-0.5 rounded bg-dark-700 text-[10px]">F</kbd> Filters
          <kbd className="ml-2 px-1 py-0.5 rounded bg-dark-700 text-[10px]">Esc</kbd> Close
          <kbd className="ml-2 px-1 py-0.5 rounded bg-dark-700 text-[10px]">Ctrl+Z</kbd> Undo
        </span>
      </div>
    </div>
  )
}
