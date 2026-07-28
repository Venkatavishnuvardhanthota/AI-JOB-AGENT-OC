import { useState, useMemo, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { RefreshCw, Settings } from 'lucide-react'
import { ProviderCard } from '@/components/provider-management/ProviderCard'
import { ProviderDetailsDrawer } from '@/components/provider-management/ProviderDetailsDrawer'
import { ProviderBulkActions } from '@/components/provider-management/ProviderBulkActions'
import { ProviderFilters } from '@/components/provider-management/ProviderFilters'
import { DiscoveryConfiguration } from '@/components/provider-management/DiscoveryConfiguration'
import { providerManagementService } from '@/services/provider-management'
import type { ManagedProvider, ProviderFilterOptions, ProviderCategory } from '@/services/provider-management'
import type { ProviderId } from '@/services/discovery/types'

const DEFAULT_FILTERS: ProviderFilterOptions = {
  search: '',
  categories: [],
  regions: [],
  countries: [],
  healthStatuses: [],
  capabilities: [],
  enabled: null,
  sortBy: 'priority',
  sortOrder: 'asc',
}

export function ProviderManagementPage() {
  const [providers, setProviders] = useState<ManagedProvider[]>(() => providerManagementService.getProviders())
  const [categories] = useState<ProviderCategory[]>(() => providerManagementService.getCategories())
  const [filters, setFilters] = useState<ProviderFilterOptions>(DEFAULT_FILTERS)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [drawerProvider, setDrawerProvider] = useState<ManagedProvider | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [showConfig, setShowConfig] = useState(false)
  const [healthRunning, setHealthRunning] = useState(false)

  const refresh = useCallback(() => {
    setProviders(providerManagementService.getProviders())
  }, [])

  const filteredProviders = useMemo(() => {
    return providerManagementService.getFilteredProviders(filters)
  }, [providers, filters])

  const handleToggle = useCallback((id: string, enabled: boolean) => {
    const providerId = id as ProviderId
    if (enabled) {
      providerManagementService.enableProvider(providerId)
    } else {
      providerManagementService.disableProvider(providerId)
    }
    refresh()
  }, [refresh])

  const handleBulkAction = useCallback((action: 'enable' | 'disable' | 'healthCheck') => {
    const ids = Array.from(selectedIds) as ProviderId[]
    if (action === 'healthCheck') {
      ids.forEach(id => providerManagementService.runHealthCheck(id))
    } else {
      providerManagementService.bulkAction(action, ids)
    }
    setSelectedIds(new Set())
    setHealthRunning(true)
    setTimeout(() => {
      refresh()
      setHealthRunning(false)
    }, action === 'healthCheck' ? 2000 : 500)
  }, [selectedIds, refresh])

  const handleCardClick = useCallback((id: string) => {
    const p = providers.find(pr => pr.id === id)
    if (p) {
      setDrawerProvider(p)
      setDrawerOpen(true)
    }
  }, [providers])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Provider Management</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage, monitor, and configure all job platform providers
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="outline" onClick={() => { setShowConfig(!showConfig); }}>
            <Settings className="h-4 w-4 mr-1" /> Configuration
          </Button>
          <Button size="sm" variant="outline" onClick={refresh} disabled={healthRunning}>
            <RefreshCw className={`h-4 w-4 mr-1 ${healthRunning ? 'animate-spin' : ''}`} /> Refresh
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
        <div className="space-y-4 lg:col-span-1">
          <ProviderFilters
            filters={filters}
            categories={categories}
            onFiltersChange={setFilters}
          />

          {showConfig && <DiscoveryConfiguration />}
        </div>

        <div className="space-y-4 lg:col-span-3">
          <ProviderBulkActions
            selectedCount={selectedIds.size}
            onBulkAction={handleBulkAction}
          />

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {filteredProviders.map(provider => (
              <ProviderCard
                key={provider.id}
                provider={provider}
                onToggle={handleToggle}
                onClick={handleCardClick}
              />
            ))}
          </div>

          {filteredProviders.length === 0 && (
            <div className="text-center py-12">
              <p className="text-sm text-muted-foreground">No providers found</p>
            </div>
          )}

          <p className="text-xs text-muted-foreground text-center">
            Showing {filteredProviders.length} of {providers.length} providers
          </p>
        </div>
      </div>

      <ProviderDetailsDrawer
        provider={drawerProvider}
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
        onToggle={handleToggle}
      />
    </div>
  )
}
