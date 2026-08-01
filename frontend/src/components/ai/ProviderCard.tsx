import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ProviderStatusBadge } from '@/components/ai/ProviderStatusBadge'
import { ProviderCapabilities } from '@/components/ai/ProviderCapabilities'
import { useToast } from '@/components/ui/toast'
import { useTestAIConnection } from '@/api/hooks'
import type { AIProvider } from '@/types'
import {
  CheckCircle2,
  XCircle,
  Loader2,
  RefreshCw,
  Activity,
  Settings,
} from 'lucide-react'

interface ProviderCardProps {
  provider: AIProvider
  onRefreshModels: (name: string) => void
  onConfigure: (name: string) => void
}

export function ProviderCard({ provider, onRefreshModels, onConfigure }: ProviderCardProps) {
  const { addToast } = useToast()
  const testMutation = useTestAIConnection()
  const [testResult, setTestResult] = useState<{ healthy: boolean; latency_ms?: number; error?: string } | null>(null)

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
            <span className="text-muted-foreground">Models</span>
            <span>{provider.models?.length || 0} available</span>
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
          <Button size="sm" variant="outline" onClick={() => onRefreshModels(provider.name)}>
            <RefreshCw className="h-3 w-3 mr-1" />
            Models
          </Button>
          <Button size="sm" variant="outline" onClick={() => onConfigure(provider.name)}>
            <Settings className="h-3 w-3 mr-1" />
            Configure
          </Button>
        </div>
      </CardContent>
    </Card>
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
