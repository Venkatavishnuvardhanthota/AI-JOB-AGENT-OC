import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { ProviderStatusBadge } from '@/components/ai/ProviderStatusBadge'
import { ProviderCapabilities } from '@/components/ai/ProviderCapabilities'
import { useToast } from '@/components/ui/toast'
import { useTestAIConnection, useAIModels } from '@/api/hooks'
import type { AIProvider } from '@/types'
import {
  CheckCircle2,
  XCircle,
  Loader2,
  RefreshCw,
  Activity,
  Settings,
  Layers,
  X,
} from 'lucide-react'

interface ProviderCardProps {
  provider: AIProvider
  onConfigure: (name: string) => void
}

export function ProviderCard({ provider, onConfigure }: ProviderCardProps) {
  const { addToast } = useToast()
  const testMutation = useTestAIConnection()
  const [testResult, setTestResult] = useState<{ healthy: boolean; latency_ms?: number; error?: string } | null>(null)
  const [modelsOpen, setModelsOpen] = useState(false)

  const handleTest = async () => {
    setTestResult(null)
    testMutation.mutate(provider.name, {
      onSuccess: (data) => {
        setTestResult({ healthy: data.healthy, latency_ms: data.latency_ms, error: data.error })
        addToast(data.healthy ? `${provider.display_name} connected (${data.latency_ms?.toFixed(0)}ms)` : `Connection failed: ${data.error}`, data.healthy ? 'success' : 'error')
      },
      onError: (err: Error) => {
        setTestResult({ healthy: false, error: err.message })
        addToast(`Test failed: ${err.message}`, 'error')
      },
    })
  }

  const statusBadges = (
    <div className="flex flex-wrap gap-1">
      {provider.configured && <ProviderStatusBadge type="configured" />}
      {provider.is_default && <ProviderStatusBadge type="default" />}
      {provider.is_available ? <ProviderStatusBadge type="healthy" /> : <ProviderStatusBadge type="unavailable" />}
      {provider.error && <ProviderStatusBadge type="error" label="Error" />}
    </div>
  )

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-base">{provider.display_name}</CardTitle>
            {provider.description && (
              <p className="text-xs text-muted-foreground mt-0.5">{provider.description}</p>
            )}
          </div>
          <div className="flex items-center gap-1 shrink-0">
            {provider.version && (
              <span className="text-[10px] text-muted-foreground">v{provider.version}</span>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {statusBadges}

        <div className="text-xs space-y-1">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Status</span>
            <span className={provider.is_available ? 'text-success' : 'text-error'}>
              {provider.is_available ? 'Available' : 'Unavailable'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Streaming</span>
            <span>{provider.supports_streaming ? 'Supported' : 'Not supported'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">API Key</span>
            <span>{provider.saved_config?.api_key_set ? 'Saved' : 'Not set'}</span>
          </div>
        </div>

        <div>
          <p className="text-xs text-muted-foreground mb-1">Capabilities</p>
          <ProviderCapabilities capabilities={provider.capabilities} />
        </div>

        {testResult && (
          <div className={`text-xs flex items-center gap-1 ${testResult.healthy ? 'text-success' : 'text-error'}`}>
            {testResult.healthy ? <CheckCircle2 className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
            {testResult.healthy
              ? `Connected (${testResult.latency_ms?.toFixed(0)}ms)`
              : testResult.error || 'Connection failed'}
          </div>
        )}

        <div className="flex flex-wrap gap-1.5 pt-1">
          <Button size="sm" variant="outline" onClick={handleTest} disabled={testMutation.isPending}>
            {testMutation.isPending ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <Activity className="h-3 w-3 mr-1" />}
            Test
          </Button>
          <Button size="sm" variant="outline" onClick={() => setModelsOpen(true)}>
            <Layers className="h-3 w-3 mr-1" />
            Models
          </Button>
          <Button size="sm" variant="outline" onClick={() => onConfigure(provider.name)}>
            <Settings className="h-3 w-3 mr-1" />
            Configure
          </Button>
        </div>
      </CardContent>

      {modelsOpen && <ProviderModelsDialog provider={provider} onClose={() => setModelsOpen(false)} />}
    </Card>
  )
}

function ProviderModelsDialog({ provider, onClose }: { provider: AIProvider; onClose: () => void }) {
  const { data: models, isLoading, isError, refetch, isFetching } = useAIModels(provider.name)

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-16" onClick={onClose}>
      <div className="absolute inset-0 bg-black/50" />
      <div
        className="relative z-10 w-full max-w-lg rounded-xl border border-glass-border bg-dark-900 shadow-xl max-h-[80vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-glass-border">
          <div>
            <h3 className="text-lg font-semibold">{provider.display_name} Models</h3>
            <p className="text-xs text-muted-foreground">Fetched live from the provider API</p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}><X className="h-4 w-4" /></Button>
        </div>
        <div className="p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">{models?.length || 0} models available</span>
            <Button size="sm" variant="outline" onClick={() => refetch()} disabled={isFetching}>
              <RefreshCw className={`h-3 w-3 mr-1 ${isFetching ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
          {isLoading && (
            <div className="space-y-2">
              {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-10 w-full" />)}
            </div>
          )}
          {isError && (
            <p className="text-sm text-error">Failed to fetch models. The provider may be unreachable.</p>
          )}
          {!isLoading && !isError && (
            <ul className="space-y-1.5">
              {(models || []).map((m: any) => (
                <li key={m.id} className="flex items-center justify-between gap-2 rounded-md border border-glass-border p-2 text-sm">
                  <div className="min-w-0">
                    <p className="truncate font-medium">{m.name || m.id}</p>
                    <p className="truncate text-xs text-muted-foreground">{m.id}</p>
                  </div>
                  <div className="flex shrink-0 flex-wrap gap-1">
                    {m.supports_streaming && <Badge variant="outline">streaming</Badge>}
                    {m.supports_vision && <Badge variant="outline">vision</Badge>}
                    {m.supports_function_calling && <Badge variant="outline">tools</Badge>}
                  </div>
                </li>
              ))}
              {!isLoading && !isError && models?.length === 0 && (
                <p className="text-sm text-muted-foreground">No models returned by this provider.</p>
              )}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}

export function ProviderCardSkeleton() {
  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-3">
        <Skeleton className="h-5 w-32 mb-1" />
        <Skeleton className="h-3 w-48" />
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-1"><Skeleton className="h-5 w-16" /><Skeleton className="h-5 w-16" /></div>
        {[1, 2, 3].map(i => <Skeleton key={i} className="h-3 w-full" />)}
        <Skeleton className="h-4 w-24" />
        <div className="flex gap-1"><Skeleton className="h-8 w-16" /><Skeleton className="h-8 w-16" /><Skeleton className="h-8 w-20" /></div>
      </CardContent>
    </Card>
  )
}
