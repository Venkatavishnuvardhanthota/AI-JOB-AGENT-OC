import { useEffect, useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Activity, Clock, Star, MapPin, Globe, Shield, Power, PowerOff, RefreshCw, Search, Trash2, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ManagedProvider, ProviderDetails } from '@/services/provider-management'
import type { SearchResult } from '@/services/discovery/types'
import { providerManagementService } from '@/services/provider-management'

interface ProviderDetailsDrawerProps {
  provider: ManagedProvider | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onToggle: (id: string, enabled: boolean) => void
}

export function ProviderDetailsDrawer({ provider, open, onOpenChange, onToggle }: ProviderDetailsDrawerProps) {
  const [details, setDetails] = useState<ProviderDetails | null>(null)
  const [healthRunning, setHealthRunning] = useState(false)
  const [searchRunning, setSearchRunning] = useState(false)
  const [searchResult, setSearchResult] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('metadata')

  useEffect(() => {
    if (provider && open) {
      try {
        setDetails(providerManagementService.getProviderDetails(provider.id))
      } catch {
        setDetails(null)
      }
    } else {
      setDetails(null)
      setSearchResult(null)
    }
  }, [provider, open])

  if (!open || !provider) return null

  const handleHealthCheck = async () => {
    setHealthRunning(true)
    try {
      await providerManagementService.runHealthCheck(provider.id)
    } finally {
      setHealthRunning(false)
      if (open && provider) {
        try {
          setDetails(providerManagementService.getProviderDetails(provider.id))
        } catch {}
      }
    }
  }

  const handleTestSearch = async () => {
    setSearchRunning(true)
    setSearchResult(null)
    try {
      const result = await providerManagementService.testSearch(provider.id)
      const r = result as SearchResult
      if (r.error) {
        setSearchResult(`Error: ${r.error}`)
      } else {
        setSearchResult(`Found ${r.jobs.length} jobs in ${r.duration}ms`)
      }
    } catch (err) {
      setSearchResult(`Error: ${err instanceof Error ? err.message : 'Unknown'}`)
    } finally {
      setSearchRunning(false)
    }
  }

  const handleReset = () => {
    providerManagementService.resetProvider(provider.id)
    if (open && provider) {
      try {
        setDetails(providerManagementService.getProviderDetails(provider.id))
      } catch {}
    }
  }

  const tabs = ['metadata', 'health', 'metrics']

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/50" onClick={() => onOpenChange(false)} />
      <div className="relative z-10 w-full max-w-lg bg-dark-900 border-l border-glass-border overflow-y-auto">
        <div className="sticky top-0 bg-dark-900 border-b border-glass-border px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2 min-w-0">
            <h2 className="font-semibold text-sm truncate">{provider.name}</h2>
            <Badge variant="outline" className="text-[10px] shrink-0">v{provider.version}</Badge>
            <Badge
              variant="outline"
              className={cn(
                'text-[10px] shrink-0',
                provider.health.status === 'healthy' ? 'text-success border-success/30' :
                provider.health.status === 'degraded' ? 'text-warning border-warning/30' :
                'text-error border-error/30'
              )}
            >
              <Activity className="h-2.5 w-2.5 mr-1" />
              {provider.health.status}
            </Badge>
          </div>
          <Button variant="ghost" size="icon" onClick={() => onOpenChange(false)}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="p-4 space-y-4">
          <p className="text-xs text-muted-foreground">{provider.category}</p>

          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant={provider.enabled ? 'destructive' : 'default'} onClick={() => onToggle(provider.id, !provider.enabled)}>
              {provider.enabled ? <PowerOff className="h-3 w-3 mr-1" /> : <Power className="h-3 w-3 mr-1" />}
              {provider.enabled ? 'Disable' : 'Enable'}
            </Button>
            <Button size="sm" variant="outline" onClick={handleHealthCheck} disabled={healthRunning}>
              <RefreshCw className={cn('h-3 w-3 mr-1', healthRunning && 'animate-spin')} />
              Health Check
            </Button>
            <Button size="sm" variant="outline" onClick={handleTestSearch} disabled={searchRunning}>
              <Search className={cn('h-3 w-3 mr-1', searchRunning && 'animate-spin')} />
              Test Search
            </Button>
            <Button size="sm" variant="ghost" onClick={handleReset}>
              <Trash2 className="h-3 w-3 mr-1" />
              Reset
            </Button>
          </div>

          {searchResult && (
            <div className="p-2 rounded bg-dark-800 text-xs text-muted-foreground">
              {searchResult}
            </div>
          )}

          <div className="flex border-b border-glass-border">
            {tabs.map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={cn(
                  'px-3 py-2 text-xs font-medium capitalize border-b-2 transition-colors',
                  activeTab === tab ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'
                )}
              >
                {tab}
              </button>
            ))}
          </div>

          {activeTab === 'metadata' && details && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-xs text-muted-foreground">Region</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {provider.metadata.region.map(r => (
                      <Badge key={r} variant="secondary" className="text-[10px]"><Globe className="h-2.5 w-2.5 mr-1" />{r}</Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Countries</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {provider.metadata.country.map(c => (
                      <Badge key={c} variant="outline" className="text-[10px]"><MapPin className="h-2.5 w-2.5 mr-1" />{c.toUpperCase()}</Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Job Types</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {provider.metadata.jobTypes.map(j => (
                      <Badge key={j} variant="secondary" className="text-[10px]">{j}</Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Priority</p>
                  <p className="font-mono text-sm mt-1">P{provider.priority}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Estimated Latency</p>
                  <p className="font-mono text-sm mt-1 flex items-center gap-1"><Clock className="h-3 w-3" />{provider.metadata.estimatedLatency}ms</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Reliability</p>
                  <p className="font-mono text-sm mt-1 flex items-center gap-1"><Star className="h-3 w-3" />{Math.round(provider.metadata.reliabilityScore * 100)}%</p>
                </div>
              </div>

              <Separator />

              <div>
                <p className="text-xs text-muted-foreground mb-2">Capabilities</p>
                <div className="flex flex-wrap gap-1">
                  {provider.metadata.capabilitySupport.map(c => (
                    <Badge key={c} variant="outline" className="text-[10px]"><Shield className="h-2.5 w-2.5 mr-1" />{c}</Badge>
                  ))}
                </div>
              </div>

              <Separator />

              <div>
                <p className="text-xs text-muted-foreground mb-2">Features</p>
                <div className="flex flex-wrap gap-1">
                  {provider.metadata.featureSupport.map(f => (
                    <Badge key={f} variant="secondary" className="text-[10px]">{f}</Badge>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'health' && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-xs text-muted-foreground">Status</p>
                  <p className="font-mono text-sm mt-1">{provider.health.status}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Success Rate</p>
                  <p className="font-mono text-sm mt-1">{Math.round(provider.health.successRate * 100)}%</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Availability</p>
                  <p className="font-mono text-sm mt-1">{Math.round(provider.health.availability * 100)}%</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Avg Latency</p>
                  <p className="font-mono text-sm mt-1">{provider.health.averageLatency}ms</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Consecutive Failures</p>
                  <p className="font-mono text-sm mt-1">{provider.health.consecutiveFailures}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Error Count</p>
                  <p className="font-mono text-sm mt-1">{provider.health.errorCount}</p>
                </div>
              </div>

              {provider.health.lastSuccess && (
                <div>
                  <p className="text-xs text-muted-foreground">Last Success</p>
                  <p className="font-mono text-xs mt-1">{new Date(provider.health.lastSuccess).toLocaleString()}</p>
                </div>
              )}
              {provider.health.lastFailure && (
                <div>
                  <p className="text-xs text-muted-foreground">Last Failure</p>
                  <p className="font-mono text-xs mt-1">{new Date(provider.health.lastFailure).toLocaleString()}</p>
                </div>
              )}
              {provider.health.lastError && (
                <div>
                  <p className="text-xs text-muted-foreground">Last Error</p>
                  <p className="font-mono text-xs mt-1 text-error">{provider.health.lastError}</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'metrics' && details && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-xs text-muted-foreground">Average Latency</p>
                  <p className="font-mono text-sm mt-1">{details.metrics.averageLatency}ms</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Success Rate</p>
                  <p className="font-mono text-sm mt-1">{Math.round(details.metrics.successRate * 100)}%</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Failure Rate</p>
                  <p className="font-mono text-sm mt-1">{Math.round(details.metrics.failureRate * 100)}%</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Retry Count</p>
                  <p className="font-mono text-sm mt-1">{details.metrics.retryCount}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Search Count</p>
                  <p className="font-mono text-sm mt-1">{details.metrics.searchCount}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Jobs Returned</p>
                  <p className="font-mono text-sm mt-1">{details.metrics.jobsReturned}</p>
                </div>
              </div>

              {details.recentSearches.length > 0 && (
                <>
                  <Separator />
                  <div>
                    <p className="text-xs text-muted-foreground mb-2">Recent Searches</p>
                    <div className="space-y-1">
                      {details.recentSearches.slice(0, 5).map((s, i) => (
                        <div key={i} className="flex justify-between text-xs">
                          <span className="text-muted-foreground truncate max-w-[200px]">{s.query}</span>
                          <span className="font-mono">{s.jobsFound} jobs</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {details.logs.length > 0 && (
                <>
                  <Separator />
                  <div>
                    <p className="text-xs text-muted-foreground mb-2">Recent Logs</p>
                    <div className="space-y-1 max-h-40 overflow-y-auto">
                      {details.logs.slice(0, 10).map((log, i) => (
                        <div key={i} className="flex gap-2 text-[10px] font-mono">
                          <span className={cn(
                            'shrink-0',
                            log.level === 'error' ? 'text-error' : log.level === 'warn' ? 'text-warning' : 'text-muted-foreground'
                          )}>
                            {log.level.toUpperCase()}
                          </span>
                          <span className="text-muted-foreground truncate">{log.message}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
