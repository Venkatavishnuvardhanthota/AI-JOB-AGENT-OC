import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { SlidersHorizontal, X } from 'lucide-react'
import type { DiscoveryFilters, ProviderId, RemotePreference, ExperienceLevel, EmploymentType } from '@/services/discovery'

interface FiltersPanelProps {
  filters: DiscoveryFilters
  onFilterChange: (filters: DiscoveryFilters) => void
  availableProviders: ProviderId[]
}

export function FiltersPanel({ filters, onFilterChange, availableProviders }: FiltersPanelProps) {
  const update = (updates: Partial<DiscoveryFilters>) => {
    onFilterChange({ ...filters, ...updates })
  }

  const clearFilters = () => {
    onFilterChange({
      providers: [],
      companies: [],
      locations: [],
      remote: null,
      salaryMin: null,
      salaryMax: null,
      experienceLevel: null,
      employmentType: null,
      skills: [],
      postedWithinDays: null,
      easyApplyOnly: false,
      tags: [],
    })
  }

  const hasActiveFilters = filters.providers.length > 0 || filters.companies.length > 0 || filters.locations.length > 0 ||
    filters.remote !== null || filters.salaryMin !== null || filters.salaryMax !== null ||
    filters.experienceLevel !== null || filters.employmentType !== null || filters.skills.length > 0 ||
    filters.postedWithinDays !== null || filters.easyApplyOnly || filters.tags.length > 0

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg flex items-center gap-2">
          <SlidersHorizontal className="w-5 h-5" />
          Filters
        </CardTitle>
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" className="h-6 text-xs" onClick={clearFilters}>
            <X className="w-3 h-3 mr-1" /> Clear
          </Button>
        )}
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Providers</label>
            <Select
              multiple
              value={filters.providers}
              onChange={e => update({ providers: Array.from(e.target.selectedOptions, o => o.value as ProviderId) })}
              className="w-full text-sm"
            >
              {availableProviders.map(p => (
                <option key={p} value={p}>{p.replace(/_/g, ' ')}</option>
              ))}
            </Select>
          </div>

          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Remote</label>
            <Select value={filters.remote || ''} onChange={e => update({ remote: (e.target.value || null) as RemotePreference | null })} className="w-full text-sm">
              <option value="">Any</option>
              <option value="remote">Remote</option>
              <option value="hybrid">Hybrid</option>
              <option value="onsite">On-site</option>
            </Select>
          </div>

          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Experience Level</label>
            <Select value={filters.experienceLevel || ''} onChange={e => update({ experienceLevel: (e.target.value || null) as ExperienceLevel | null })} className="w-full text-sm">
              <option value="">Any</option>
              <option value="internship">Internship</option>
              <option value="entry">Entry Level</option>
              <option value="associate">Associate</option>
              <option value="mid_senior">Mid-Senior</option>
              <option value="director">Director</option>
              <option value="executive">Executive</option>
            </Select>
          </div>

          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Employment Type</label>
            <Select value={filters.employmentType || ''} onChange={e => update({ employmentType: (e.target.value || null) as EmploymentType | null })} className="w-full text-sm">
              <option value="">Any</option>
              <option value="full_time">Full-time</option>
              <option value="part_time">Part-time</option>
              <option value="contract">Contract</option>
              <option value="internship">Internship</option>
              <option value="freelance">Freelance</option>
            </Select>
          </div>

          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Min Salary</label>
            <Input type="number" placeholder="Min..." value={filters.salaryMin ?? ''} onChange={e => update({ salaryMin: e.target.value ? Number(e.target.value) : null })} className="text-sm" />
          </div>

          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Posted Within</label>
            <Select value={filters.postedWithinDays ?? ''} onChange={e => update({ postedWithinDays: e.target.value ? Number(e.target.value) : null })} className="w-full text-sm">
              <option value="">Any time</option>
              <option value="1">24 hours</option>
              <option value="3">3 days</option>
              <option value="7">7 days</option>
              <option value="14">14 days</option>
              <option value="30">30 days</option>
            </Select>
          </div>

          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input type="checkbox" checked={filters.easyApplyOnly} onChange={e => update({ easyApplyOnly: e.target.checked })} className="rounded" />
            Easy Apply only
          </label>
        </div>
      </CardContent>
    </Card>
  )
}
