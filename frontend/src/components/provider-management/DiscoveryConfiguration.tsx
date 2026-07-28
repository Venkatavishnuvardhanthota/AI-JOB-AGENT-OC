import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Save } from 'lucide-react'
import { providerManagementService } from '@/services/provider-management'
import type { DiscoveryConfiguration } from '@/services/provider-management'

export function DiscoveryConfiguration() {
  const [config, setConfig] = useState<DiscoveryConfiguration>(providerManagementService.getConfiguration())
  const [saved, setSaved] = useState(false)

  const update = (updates: Partial<DiscoveryConfiguration>) => {
    setConfig(prev => ({ ...prev, ...updates }))
    setSaved(false)
  }

  const handleSave = () => {
    providerManagementService.saveConfiguration(config)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm">Discovery Configuration</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Max Providers</label>
            <Input
              type="number"
              className="h-8 text-sm"
              value={config.maxProviders}
              onChange={(e) => update({ maxProviders: parseInt(e.target.value) || 20 })}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Concurrent Providers</label>
            <Input
              type="number"
              className="h-8 text-sm"
              value={config.concurrentProviders}
              onChange={(e) => update({ concurrentProviders: parseInt(e.target.value) || 5 })}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Search Timeout (ms)</label>
            <Input
              type="number"
              className="h-8 text-sm"
              value={config.searchTimeout}
              onChange={(e) => update({ searchTimeout: parseInt(e.target.value) || 30000 })}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Retry Count</label>
            <Input
              type="number"
              className="h-8 text-sm"
              value={config.retryCount}
              onChange={(e) => update({ retryCount: parseInt(e.target.value) || 2 })}
            />
          </div>
        </div>

        <Separator />

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-xs text-muted-foreground cursor-pointer">Only Healthy Providers</label>
            <input
              type="checkbox"
              className="rounded border-glass-border"
              checked={config.onlyHealthyProviders}
              onChange={(e) => update({ onlyHealthyProviders: e.target.checked })}
            />
          </div>
          <div className="flex items-center justify-between">
            <label className="text-xs text-muted-foreground cursor-pointer">Require Authentication</label>
            <input
              type="checkbox"
              className="rounded border-glass-border"
              checked={config.requireAuthentication}
              onChange={(e) => update({ requireAuthentication: e.target.checked })}
            />
          </div>
        </div>

        <Button size="sm" className="w-full" onClick={handleSave}>
          <Save className="h-3 w-3 mr-1" />
          {saved ? 'Saved!' : 'Save Configuration'}
        </Button>
      </CardContent>
    </Card>
  )
}
