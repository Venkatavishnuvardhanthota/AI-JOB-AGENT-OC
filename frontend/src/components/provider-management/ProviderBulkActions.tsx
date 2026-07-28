import { Button } from '@/components/ui/button'
import { Power, PowerOff, RefreshCw, CheckSquare } from 'lucide-react'

interface ProviderBulkActionsProps {
  selectedCount: number
  onBulkAction: (action: 'enable' | 'disable' | 'healthCheck') => void
}

export function ProviderBulkActions({ selectedCount, onBulkAction }: ProviderBulkActionsProps) {
  if (selectedCount === 0) return null

  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-primary/5 border border-primary/10">
      <CheckSquare className="h-4 w-4 text-primary" />
      <span className="text-sm text-muted-foreground mr-2">{selectedCount} selected</span>
      <Button size="sm" variant="outline" className="h-7 text-xs" onClick={() => onBulkAction('enable')}>
        <Power className="h-3 w-3 mr-1" /> Enable
      </Button>
      <Button size="sm" variant="outline" className="h-7 text-xs" onClick={() => onBulkAction('disable')}>
        <PowerOff className="h-3 w-3 mr-1" /> Disable
      </Button>
      <Button size="sm" variant="outline" className="h-7 text-xs" onClick={() => onBulkAction('healthCheck')}>
        <RefreshCw className="h-3 w-3 mr-1" /> Health Check
      </Button>
    </div>
  )
}
