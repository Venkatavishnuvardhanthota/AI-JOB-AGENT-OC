import { useState } from 'react'
import { Button } from '@/components/ui/button'

import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuSeparator,
  DropdownMenuItem,
} from '@/components/ui/dropdown-menu'
import { getStatusLabel } from '@/services/status'
import { preferenceService } from '@/services/preferences'
import type { ApplicationStatus } from '@/types'
import { Settings2, Eye, EyeOff, GripVertical, ChevronUp, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ColumnCustomizerProps {
  statuses: ApplicationStatus[]
  visibility: Record<string, boolean>
  onVisibilityChange: (visibility: Record<string, boolean>) => void
  onReorder: (statuses: ApplicationStatus[]) => void
}

export function ColumnCustomizer({ statuses, visibility, onVisibilityChange, onReorder }: ColumnCustomizerProps) {
  const [open, setOpen] = useState(false)

  const moveColumn = (index: number, direction: -1 | 1) => {
    const newOrder = [...statuses]
    const target = index + direction
    if (target < 0 || target >= newOrder.length) return
    const temp = newOrder[target]
    newOrder[target] = newOrder[index]
    newOrder[index] = temp
    onReorder(newOrder)
    preferenceService.setColumnOrder(newOrder)
  }

  const toggleVisibility = (status: string) => {
    const updated = { ...visibility, [status]: visibility[status] === false ? true : false }
    onVisibilityChange(updated)
    preferenceService.setColumnVisibility(updated)
  }

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" aria-label="Customize columns">
          <Settings2 className="h-4 w-4 mr-1" /> Columns
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64 max-h-80 overflow-y-auto">
        <div className="px-2 py-1.5 text-sm font-medium">Customize Columns</div>
        <DropdownMenuSeparator />
        {statuses.map((status, index) => (
          <div key={status} className={cn(
            'flex items-center gap-2 px-2 py-1.5 text-sm',
            !visibility[status] && 'opacity-40'
          )}>
            <button
              onClick={() => moveColumn(index, -1)}
              disabled={index === 0}
              className="p-0.5 hover:text-foreground disabled:opacity-20"
              aria-label={`Move ${getStatusLabel(status)} left`}
            >
              <ChevronUp className="h-3 w-3" />
            </button>
            <button
              onClick={() => moveColumn(index, 1)}
              disabled={index === statuses.length - 1}
              className="p-0.5 hover:text-foreground disabled:opacity-20"
              aria-label={`Move ${getStatusLabel(status)} right`}
            >
              <ChevronDown className="h-3 w-3" />
            </button>
            <GripVertical className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="flex-1 truncate">{getStatusLabel(status)}</span>
            <button
              onClick={() => toggleVisibility(status)}
              className={cn(
                'px-2 py-0.5 text-xs rounded transition-colors',
                visibility[status] !== false
                  ? 'bg-primary/10 text-primary'
                  : 'bg-dark-700 text-muted-foreground'
              )}
              aria-label={`Show ${getStatusLabel(status)} column`}
            >
              {visibility[status] !== false ? 'Visible' : 'Hidden'}
            </button>
          </div>
        ))}
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => {
          const all: Record<string, boolean> = {}
          statuses.forEach(s => { all[s] = true })
          onVisibilityChange(all)
          preferenceService.setColumnVisibility(all)
        }}>
          <Eye className="h-4 w-4 mr-2" /> Show all columns
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => {
          const none: Record<string, boolean> = {}
          statuses.forEach(s => { none[s] = false })
          onVisibilityChange(none)
          preferenceService.setColumnVisibility(none)
        }}>
          <EyeOff className="h-4 w-4 mr-2" /> Hide all columns
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
