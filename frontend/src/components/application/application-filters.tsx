import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { SavedFilters } from './saved-filters'
import { RecentSearches } from './recent-searches'
import { Search, X } from 'lucide-react'
import { APPLICATION_STATUSES, PRIORITY_ORDER, PRIORITY_LABELS, getStatusLabel } from '@/services/status'

export interface FilterValues {
  search: string
  status: string
  priority: string
  company: string
  location: string
  recruiter: string
  date_from: string
  date_to: string
}

interface ApplicationFiltersProps {
  values: FilterValues
  onChange: (values: FilterValues) => void
  onReset: () => void
}

export function ApplicationFilters({ values, onChange, onReset }: ApplicationFiltersProps) {
  const update = (key: keyof FilterValues, val: string) => {
    onChange({ ...values, [key]: val })
  }

  const hasFilters = values.search || values.status || values.priority || values.company ||
    values.location || values.recruiter || values.date_from || values.date_to

  return (
    <div className="space-y-3">
      <SavedFilters currentFilters={values} onApply={onChange} />

      <RecentSearches currentFilters={values} onApply={onChange} />

      <div className="relative">
        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search by company, role, or location... (press / to focus)"
          value={values.search}
          onChange={(e) => update('search', e.target.value)}
          className="pl-8"
          aria-label="Search applications"
        />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Select
          value={values.status}
          onChange={(e) => update('status', e.target.value)}
          aria-label="Filter by status"
        >
          <option value="">All Statuses</option>
          {APPLICATION_STATUSES.map(s => (
            <option key={s} value={s}>{getStatusLabel(s)}</option>
          ))}
        </Select>
        <Select
          value={values.priority}
          onChange={(e) => update('priority', e.target.value)}
          aria-label="Filter by priority"
        >
          <option value="">All Priorities</option>
          {PRIORITY_ORDER.map(p => (
            <option key={p} value={p}>{PRIORITY_LABELS[p]}</option>
          ))}
        </Select>
        <Input
          placeholder="Company..."
          value={values.company}
          onChange={(e) => update('company', e.target.value)}
          aria-label="Filter by company"
        />
        <Input
          placeholder="Location..."
          value={values.location}
          onChange={(e) => update('location', e.target.value)}
          aria-label="Filter by location"
        />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Input
          type="date"
          value={values.date_from}
          onChange={(e) => update('date_from', e.target.value)}
          aria-label="Date from"
        />
        <Input
          type="date"
          value={values.date_to}
          onChange={(e) => update('date_to', e.target.value)}
          aria-label="Date to"
        />
        <Input
          placeholder="Recruiter..."
          value={values.recruiter}
          onChange={(e) => update('recruiter', e.target.value)}
          aria-label="Filter by recruiter"
        />
      </div>
      {hasFilters && (
        <Button variant="ghost" size="sm" onClick={onReset}>
          <X className="h-4 w-4 mr-1" /> Clear Filters
        </Button>
      )}
    </div>
  )
}
