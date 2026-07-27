import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { X, Calendar } from 'lucide-react'

export interface AnalyticsDateRange {
  from: string
  to: string
}

interface AnalyticsFiltersProps {
  dateRange: AnalyticsDateRange
  onDateRangeChange: (range: AnalyticsDateRange) => void
}

export function AnalyticsFilters({ dateRange, onDateRangeChange }: AnalyticsFiltersProps) {
  const hasFilters = dateRange.from || dateRange.to

  return (
    <div className="flex items-center gap-3 flex-wrap">
      <div className="flex items-center gap-2">
        <Calendar className="h-4 w-4 text-muted-foreground" />
        <Input
          type="date"
          value={dateRange.from}
          onChange={(e) => onDateRangeChange({ ...dateRange, from: e.target.value })}
          className="w-36 h-8 text-xs"
          aria-label="Date from"
        />
        <span className="text-xs text-muted-foreground">to</span>
        <Input
          type="date"
          value={dateRange.to}
          onChange={(e) => onDateRangeChange({ ...dateRange, to: e.target.value })}
          className="w-36 h-8 text-xs"
          aria-label="Date to"
        />
      </div>
      {hasFilters && (
        <Button variant="ghost" size="sm" className="h-8" onClick={() => onDateRangeChange({ from: '', to: '' })}>
          <X className="h-3 w-3 mr-1" /> Clear
        </Button>
      )}
    </div>
  )
}
