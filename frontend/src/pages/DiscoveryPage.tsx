import { useState, useCallback, useEffect } from 'react'
import { PageHeader } from '@/components/layout/page-header'
import { SearchPanel } from '@/components/discovery/search-panel'
import { SearchResults } from '@/components/discovery/search-results'
import { SearchProfiles } from '@/components/discovery/search-profiles'
import { ProviderStatus } from '@/components/discovery/provider-status'
import { DiscoveryHistoryPanel } from '@/components/discovery/discovery-history-panel'
import { DuplicateStats } from '@/components/discovery/duplicate-stats'
import { FiltersPanel } from '@/components/discovery/filters-panel'
import { DiscoveryDashboard } from '@/components/discovery/discovery-dashboard'
import { discoveryService } from '@/services/discovery/discovery'
import { discoveryHistoryService } from '@/services/discovery/discovery-history'
import { providerHealthService } from '@/services/discovery/provider-health'
import { searchProfileService } from '@/services/discovery/search-profile'
import { applyFilters } from '@/services/discovery/filters'
import type { DiscoveryResult, DiscoveryHistoryEntry, DiscoveryFilters, SearchProfile, ProviderHealth, ProviderId, ScheduleFrequency } from '@/services/discovery/types'

export function DiscoveryPage() {
  const [isSearching, setIsSearching] = useState(false)
  const [result, setResult] = useState<DiscoveryResult | null>(null)
  const [history, setHistory] = useState<DiscoveryHistoryEntry[]>([])
  const [profiles, setProfiles] = useState<SearchProfile[]>([])
  const [providerHealth, setProviderHealth] = useState<Record<ProviderId, ProviderHealth>>({} as Record<ProviderId, ProviderHealth>)
  const [filters, setFilters] = useState<DiscoveryFilters>({
    providers: [], companies: [], locations: [], remote: null,
    salaryMin: null, salaryMax: null, experienceLevel: null,
    employmentType: null, skills: [], postedWithinDays: null,
    easyApplyOnly: false, tags: [],
  })

  const refreshData = useCallback(() => {
    setHistory(discoveryHistoryService.getRecent(20))
    setProfiles(searchProfileService.getAll())
    setProviderHealth(providerHealthService.getAll())
  }, [])

  useEffect(() => { refreshData() }, [refreshData])

  const handleSearch = useCallback(async (keywords: string, location: string) => {
    setIsSearching(true)
    setResult(null)
    try {
      const discResult = await discoveryService.search({
        keywords,
        location: location || null,
        remote: null,
        salaryMin: null,
        salaryMax: null,
        experienceLevel: null,
        employmentType: null,
        postedWithinDays: null,
        easyApplyOnly: false,
        page: 1,
        pageSize: 50,
      })
      setResult(discResult)
    } finally {
      setIsSearching(false)
      refreshData()
    }
  }, [refreshData])

  const handleProfileRun = useCallback(async (profileId: string) => {
    setIsSearching(true)
    setResult(null)
    try {
      const discResult = await discoveryService.searchProfile(profileId)
      setResult(discResult)
    } finally {
      setIsSearching(false)
      refreshData()
    }
  }, [refreshData])

  const handleProfileCreate = useCallback((name: string, keywords: string, location: string | null, schedule: ScheduleFrequency) => {
    const enabledProviders = providerHealth ? Object.keys(providerHealth) as ProviderId[] : []
    searchProfileService.create({
      name, keywords, location,
      salaryMin: null, salaryMax: null,
      experienceLevel: null, employmentType: null,
      remote: null,
      enabledProviders,
      scheduleFrequency: schedule,
    })
    refreshData()
  }, [providerHealth, refreshData])

  const handleProfileDelete = useCallback((id: string) => {
    searchProfileService.remove(id)
    refreshData()
  }, [refreshData])

  const filteredJobs = result ? applyFilters(result.jobs, filters) : []

  const availableProviders = result
    ? [...new Set(result.jobs.map(j => j.provider))]
    : []

  const statistics = discoveryHistoryService.getStatistics()

  return (
    <div className="space-y-6">
      <PageHeader
        title="Job Discovery"
        description="Search across multiple job platforms, save searches, and track provider health."
      />

      <DiscoveryDashboard statistics={statistics} />

      <SearchPanel onSearch={handleSearch} isSearching={isSearching} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {result && (
            <>
              <DuplicateStats
                totalJobs={result.jobsFound}
                uniqueJobs={result.uniqueJobs}
                duplicatesRemoved={result.duplicatesRemoved}
              />
              <SearchResults
                jobs={filteredJobs}
                totalFound={result.jobsFound}
                duplicatesRemoved={result.duplicatesRemoved}
                executionTime={result.executionTime}
                isLoading={false}
              />
            </>
          )}
          {!result && !isSearching && (
            <div className="text-center py-12 text-muted-foreground">
              <p>Enter keywords above to discover jobs from multiple providers.</p>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <FiltersPanel
            filters={filters}
            onFilterChange={setFilters}
            availableProviders={availableProviders}
          />
          <SearchProfiles
            profiles={profiles}
            onCreate={handleProfileCreate}
            onRun={handleProfileRun}
            onDelete={handleProfileDelete}
            isSearching={isSearching}
          />
          <ProviderStatus health={providerHealth} />
          <DiscoveryHistoryPanel entries={history} />
        </div>
      </div>
    </div>
  )
}
