import { useMemo, useCallback, useRef, useState } from 'react'
import { getStatusLabel } from '@/services/status'
import { preferenceService } from '@/services/preferences'
import { evaluateColumnRule, DEFAULT_COLUMN_RULES, getColumnValidation } from '@/services/pipeline'
import { WipIndicators } from './wip-indicators'
import { KanbanCard } from './kanban-card'
import { cn } from '@/lib/utils'
import type { Application, ApplicationStatus } from '@/types'
import type { ColumnRuleResult } from '@/services/pipeline'
import { ChevronDown, ChevronRight } from 'lucide-react'

interface KanbanColumnProps {
  status: ApplicationStatus
  applications: Application[]
  onDrop: (applicationId: string, toStatus: ApplicationStatus) => void
  onPreview: (application: Application) => void
  selectedIds: string[]
  onSelect: (id: string, shiftKey: boolean) => void
}

export function KanbanColumn({ status, applications, onDrop, onPreview, selectedIds, onSelect }: KanbanColumnProps) {
  const [collapsed, setCollapsed] = useState(() => preferenceService.isColumnCollapsed(status))
  const columnRef = useRef<HTMLDivElement>(null)

  const validation = useMemo(() => getColumnValidation(applications, status), [applications, status])

  const columnRules: ColumnRuleResult[] = useMemo(() => {
    return DEFAULT_COLUMN_RULES
      .filter(r => r.column === status && r.enabled)
      .map(r => evaluateColumnRule(r, applications, validation))
      .filter((r): r is ColumnRuleResult => r !== null)
  }, [applications, validation, status])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const appId = e.dataTransfer.getData('text/plain')
    if (appId) onDrop(appId, status)
  }, [status, onDrop])

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault()
  }, [])

  const toggleCollapse = useCallback(() => {
    const updated = preferenceService.toggleColumnCollapse(status)
    setCollapsed(updated[status] === true)
  }, [status])

  const hasHighPriority = validation.highPriority > 0
  const hasIssues = columnRules.length > 0

  return (
    <div
      ref={columnRef}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onDragEnter={handleDragEnter}
      role="region"
      aria-label={`${getStatusLabel(status)} column`}
      className={cn(
        'flex flex-col rounded-lg border bg-dark-900/50 min-w-[280px] max-w-[320px] transition-all duration-200',
        collapsed && 'min-w-[60px] max-w-[60px]',
      )}
    >
      <div className={cn(
        'flex items-center gap-2 px-3 py-2.5 border-b border-glass-border sticky top-0 bg-dark-900 z-10 rounded-t-lg',
        collapsed && 'flex-col px-2 py-3',
      )}>
        <button
          onClick={toggleCollapse}
          className="p-0.5 hover:text-foreground transition-colors"
          aria-label={collapsed ? `Expand ${getStatusLabel(status)} column` : `Collapse ${getStatusLabel(status)} column`}
        >
          {collapsed ? <ChevronRight className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
        </button>

        {!collapsed && (
          <>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-medium truncate">{getStatusLabel(status)}</h3>
                {hasHighPriority && (
                  <span className="w-2 h-2 rounded-full bg-destructive shrink-0" title="Has high priority items" />
                )}
                {hasIssues && (
                  <span className="w-2 h-2 rounded-full bg-warning shrink-0" title="Has column rule warnings" />
                )}
              </div>
              <WipIndicators validation={validation} rules={columnRules} />
            </div>

            <span className="text-xs text-muted-foreground tabular-nums">{applications.length}</span>
          </>
        )}

        {collapsed && (
          <div className="flex flex-col items-center gap-1">
            <span className="text-xs font-medium writing-mode-vertical">{getStatusLabel(status)}</span>
            <span className="text-xs text-muted-foreground">{applications.length}</span>
            {hasHighPriority && <span className="w-1.5 h-1.5 rounded-full bg-destructive" />}
          </div>
        )}
      </div>

      {!collapsed && (
        <div className="flex-1 overflow-y-auto p-2 space-y-2 min-h-[120px]" role="list">
          {applications.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-24 text-xs text-muted-foreground border border-dashed border-glass-border rounded-lg">
              <p>Drop cards here</p>
            </div>
          ) : (
            applications.map(app => (
              <div key={app.id} role="listitem">
                <KanbanCard
                  application={app}
                  onPreview={onPreview}
                  selected={selectedIds.includes(app.id)}
                  onSelect={onSelect}
                />
              </div>
            ))
          )}
        </div>
      )}

      {collapsed && (
        <div className="flex-1 flex items-center justify-center p-1">
          <span className="text-[10px] text-muted-foreground">{applications.length} cards</span>
        </div>
      )}
    </div>
  )
}
