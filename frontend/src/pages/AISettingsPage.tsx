import { useState } from 'react'
import { PageHeader } from '@/components/layout/page-header'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { ProviderCard, ProviderCardSkeleton } from '@/components/ai/ProviderCard'
import { ProviderConfigForm } from '@/components/ai/ProviderConfigForm'
import { AIGlobalConfig } from '@/components/ai/AIGlobalConfig'
import { HealthOverview } from '@/components/ai/HealthOverview'
import { PromptTemplatesPanel } from '@/components/ai/PromptTemplatesPanel'
import { ResumeStrategySettings } from '@/components/ai/ResumeStrategySettings'
import { useAIProviders } from '@/api/hooks'
import type { AIProvider } from '@/types'
import { RefreshCw, Server, Brain, Activity, FileText, Wand2 } from 'lucide-react'

export function AISettingsPage() {
  const { data: providers, isLoading, isError, refetch, isRefetching } = useAIProviders()
  const [configProvider, setConfigProvider] = useState<AIProvider | null>(null)
  const [configOpen, setConfigOpen] = useState(false)

  const handleConfigure = (name: string) => {
    const p = providers?.find(pr => pr.name === name)
    if (p) {
      setConfigProvider(p)
      setConfigOpen(true)
    }
  }

  const providerContent = (
    <div className="space-y-4">
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5].map(i => <ProviderCardSkeleton key={i} />)}
        </div>
      ) : isError ? (
        <div className="text-center py-12">
          <p className="text-sm text-error">Failed to load providers</p>
          <Button variant="outline" size="sm" className="mt-2" onClick={() => refetch()}>Retry</Button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
            {providers?.map(p => (
              <ProviderCard
                key={p.name}
                provider={p}
                onConfigure={handleConfigure}
              />
            ))}
          </div>
          {(!providers || providers.length === 0) && (
            <div className="text-center py-12">
              <Server className="h-12 w-12 text-muted-foreground mx-auto mb-3 opacity-50" />
              <p className="text-sm text-muted-foreground">No AI providers configured</p>
              <p className="text-xs text-muted-foreground mt-1">Configure providers in the Configuration tab</p>
            </div>
          )}
        </>
      )}
    </div>
  )

  return (
    <div className="space-y-6 max-w-5xl">
      <PageHeader
        title="AI Settings"
        description="Configure, test, and monitor AI providers"
        actions={
          <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isRefetching}>
            <RefreshCw className={`h-4 w-4 mr-1 ${isRefetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        }
      />

      <Tabs defaultValue="providers" className="space-y-4">
        <TabsList>
          <TabsTrigger value="providers">
            <Server className="h-4 w-4 mr-1.5" />
            Providers
          </TabsTrigger>
          <TabsTrigger value="config">
            <Brain className="h-4 w-4 mr-1.5" />
            Configuration
          </TabsTrigger>
          <TabsTrigger value="health">
            <Activity className="h-4 w-4 mr-1.5" />
            Live Status
          </TabsTrigger>
          <TabsTrigger value="prompts">
            <FileText className="h-4 w-4 mr-1.5" />
            Prompt Templates
          </TabsTrigger>
          <TabsTrigger value="resume-strategy">
            <Wand2 className="h-4 w-4 mr-1.5" />
            Resume Strategy
          </TabsTrigger>
        </TabsList>

        <TabsContent value="providers">
          {providerContent}
        </TabsContent>

        <TabsContent value="config">
          <div className="grid grid-cols-1 lg:grid-cols-1 gap-6">
            <AIGlobalConfig />
          </div>
        </TabsContent>

        <TabsContent value="health">
          <HealthOverview />
        </TabsContent>

        <TabsContent value="prompts">
          <PromptTemplatesPanel />
        </TabsContent>

        <TabsContent value="resume-strategy">
          <ResumeStrategySettings />
        </TabsContent>
      </Tabs>

      <ProviderConfigForm
        provider={configProvider}
        open={configOpen}
        onClose={() => { setConfigOpen(false); setConfigProvider(null) }}
      />
    </div>
  )
}
