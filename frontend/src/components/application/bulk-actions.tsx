import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { applicationService } from '@/services/application'
import { useToast } from '@/components/ui/toast'
import { APPLICATION_STATUSES, PRIORITY_ORDER, PRIORITY_LABELS, getStatusLabel } from '@/services/status'
import { Archive, Trash2, CheckSquare, FileDown, User } from 'lucide-react'

interface BulkActionsProps {
  selectedIds: string[]
  onClear: () => void
}

type BulkAction = 'status' | 'priority' | 'archive' | 'delete' | 'export' | 'recruiter'

export function BulkActions({ selectedIds, onClear }: BulkActionsProps) {
  const [action, setAction] = useState<BulkAction>('status')
  const [value, setValue] = useState('')
  const [showConfirm, setShowConfirm] = useState(false)
  const queryClient = useQueryClient()
  const { addToast } = useToast()

  const mutation = useMutation({
    mutationFn: ({ ids, act, val }: { ids: string[]; act: string; val?: string }) =>
      applicationService.bulkAction(ids, act, val),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] })
      queryClient.invalidateQueries({ queryKey: ['applications', 'stats'] })
      onClear()
      setShowConfirm(false)
      addToast(`Updated ${selectedIds.length} applications`, 'success')
    },
    onError: () => addToast('Bulk action failed', 'error'),
  })

  if (selectedIds.length === 0) return null

  const isDestructive = action === 'archive' || action === 'delete'

  const handleApply = () => {
    if (isDestructive && !showConfirm) {
      setShowConfirm(true)
      return
    }
    setShowConfirm(false)
    if (action === 'export') {
      addToast('Export feature coming soon', 'info')
      return
    }
    mutation.mutate({ ids: selectedIds, act: action, val: value || undefined })
  }

  const handleCancel = () => {
    setShowConfirm(false)
    onClear()
  }

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-primary/5 border border-primary/20" role="toolbar" aria-label="Bulk actions">
      <CheckSquare className="h-4 w-4 text-primary" />
      <span className="text-sm font-medium">{selectedIds.length} selected</span>

      <Select value={action} onChange={(e) => { setAction(e.target.value as BulkAction); setValue(''); setShowConfirm(false) }} className="w-36" aria-label="Bulk action type">
        <option value="status">Change Status</option>
        <option value="priority">Change Priority</option>
        <option value="archive">Archive</option>
        <option value="delete">Delete</option>
        <option value="export">Export</option>
        <option value="recruiter">Assign Recruiter</option>
      </Select>

      {action === 'status' && (
        <Select value={value} onChange={(e) => setValue(e.target.value)} className="w-40" aria-label="New status">
          <option value="">Select status...</option>
          {APPLICATION_STATUSES.map(s => (
            <option key={s} value={s}>{getStatusLabel(s)}</option>
          ))}
        </Select>
      )}

      {action === 'priority' && (
        <Select value={value} onChange={(e) => setValue(e.target.value)} className="w-32" aria-label="New priority">
          <option value="">Select priority...</option>
          {PRIORITY_ORDER.map(p => (
            <option key={p} value={p}>{PRIORITY_LABELS[p]}</option>
          ))}
        </Select>
      )}

      {action === 'recruiter' && (
        <Input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Recruiter name..."
          className="h-8 w-40 text-xs"
          aria-label="Recruiter name"
        />
      )}

      {(action === 'archive' || action === 'delete') && (
        <span className="text-sm text-muted-foreground">
          {action === 'archive' ? `Archive ${selectedIds.length} application(s)` : `Delete ${selectedIds.length} application(s)`}
        </span>
      )}

      {action === 'export' && (
        <span className="text-sm text-muted-foreground">Export {selectedIds.length} application(s) as CSV</span>
      )}

      {showConfirm && isDestructive ? (
        <div className="flex items-center gap-2">
          <span className="text-sm text-error font-medium">Are you sure?</span>
          <Button size="sm" variant="destructive" onClick={handleApply} disabled={mutation.isPending}>
            Confirm
          </Button>
          <Button variant="outline" size="sm" onClick={() => setShowConfirm(false)}>
            Cancel
          </Button>
        </div>
      ) : (
        <Button size="sm" onClick={handleApply} disabled={mutation.isPending || (action === 'status' && !value) || (action === 'priority' && !value)}>
          {action === 'archive' ? <Archive className="h-4 w-4 mr-1" /> : action === 'delete' ? <Trash2 className="h-4 w-4 mr-1" /> : action === 'export' ? <FileDown className="h-4 w-4 mr-1" /> : action === 'recruiter' ? <User className="h-4 w-4 mr-1" /> : <CheckSquare className="h-4 w-4 mr-1" />}
          Apply
        </Button>
      )}

      <Button variant="ghost" size="sm" onClick={handleCancel}>
        Clear
      </Button>
    </div>
  )
}
