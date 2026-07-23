import { useJobProviders } from '@/api/hooks'
import { PageHeader } from '@/components/layout/page-header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { RefreshCw, Settings } from 'lucide-react'

const providerIcons: Record<string, string> = {
  LinkedIn: 'in',
  Greenhouse: 'gh',
  Lever: 'lv',
  Ashby: 'ab',
  Wellfound: 'wf',
  Workday: 'wd',
}

export function ProvidersPage() {
  const { data: providers, isLoading } = useJobProviders()

  if (isLoading) return <div className="space-y-4">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}</div>

  return (
    <div className="space-y-6">
      <PageHeader
        title="Job Providers"
        description="Configure and manage job data providers."
        actions={
          <Button variant="outline">
            <RefreshCw className="h-4 w-4 mr-1" /> Refresh All
          </Button>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {((providers as any) || []).map((provider: any) => (
          <Card key={provider.name}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary font-bold text-sm">
                    {providerIcons[provider.name] || provider.name[0]}
                  </div>
                  <div>
                    <CardTitle className="text-base">{provider.name}</CardTitle>
                    <Badge variant={provider.status === 'enabled' ? 'success' : 'secondary'} className="text-xs">
                      {provider.status}
                    </Badge>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Jobs Found</span>
                  <span>{provider.jobs_found ?? '-'}</span>
                </div>
                {provider.error && (
                  <div className="text-xs text-error">{provider.error}</div>
                )}
              </div>
              <div className="flex gap-2 mt-4">
                <Button variant="outline" size="sm" className="flex-1"><RefreshCw className="h-3 w-3 mr-1" /> Sync</Button>
                <Button variant="outline" size="sm"><Settings className="h-3 w-3" /></Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
