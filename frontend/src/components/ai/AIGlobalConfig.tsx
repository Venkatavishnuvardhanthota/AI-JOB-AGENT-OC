import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { useToast } from '@/components/ui/toast'
import { useAIConfig, useAIProviders, useAIModels, useUpdateAIConfig } from '@/api/hooks'
import type { AIConfigData } from '@/types'
import {
  Save,
  RotateCcw,
  Loader2,
  Settings,
  CheckCircle2,
} from 'lucide-react'

export function AIGlobalConfig() {
  const { addToast } = useToast()
  const { data: config, isLoading: configLoading } = useAIConfig()
  const { data: providers } = useAIProviders()
  const updateConfig = useUpdateAIConfig()
  const [saved, setSaved] = useState(false)

  const [form, setForm] = useState<Partial<AIConfigData>>({
    default_provider: '',
    default_model: '',
    temperature: 0.7,
    max_tokens: 2048,
    timeout_seconds: 60,
    max_retries: 3,
    retry_delay_seconds: 1,
    streaming_enabled: true,
    enabled_providers: [],
  })

  const { data: models } = useAIModels(form.default_provider || undefined)

  useEffect(() => {
    if (config) {
      setForm({
        default_provider: config.default_provider || '',
        default_model: config.default_model || '',
        temperature: config.temperature ?? 0.7,
        max_tokens: config.max_tokens ?? 2048,
        timeout_seconds: config.timeout_seconds ?? 60,
        max_retries: config.max_retries ?? 3,
        retry_delay_seconds: config.retry_delay_seconds ?? 1,
        streaming_enabled: config.streaming_enabled ?? true,
        enabled_providers: config.enabled_providers || [],
      })
    }
  }, [config])

  const handleSave = () => {
    updateConfig.mutate(form, {
      onSuccess: (data) => {
        setSaved(true)
        addToast(`Configuration updated: ${data.updates.join(', ')}`, 'success')
        setTimeout(() => setSaved(false), 3000)
      },
      onError: (err: Error) => {
        addToast(`Save failed: ${err.message}`, 'error')
      },
    })
  }

  const handleReset = () => {
    setForm({
      default_provider: '',
      default_model: '',
      temperature: 0.7,
      max_tokens: 2048,
      timeout_seconds: 60,
      max_retries: 3,
      retry_delay_seconds: 1,
      streaming_enabled: true,
      enabled_providers: [],
    })
    addToast('Configuration reset to defaults', 'info')
  }

  if (configLoading) {
    return (
      <Card>
        <CardHeader><CardTitle><Skeleton className="h-5 w-40" /></CardTitle></CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-9 w-full" />)}
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings className="h-5 w-5 text-primary" />
          AI Configuration
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Default Provider</label>
            <Select
              value={form.default_provider || ''}
              onChange={e => {
                setForm(f => ({ ...f, default_provider: e.target.value, default_model: '' }))
              }}
            >
              <option value="">Select provider...</option>
              {(providers || []).map(p => (
                <option key={p.name} value={p.name}>{p.display_name}</option>
              ))}
            </Select>
          </div>
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Default Model</label>
            <Select
              value={form.default_model || ''}
              onChange={e => setForm(f => ({ ...f, default_model: e.target.value }))}
            >
              <option value="">Select model...</option>
              {(models || []).map((m: any) => (
                <option key={m.id} value={m.id}>{m.name || m.id}</option>
              ))}
            </Select>
          </div>
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Temperature</label>
            <Input
              type="number" min={0} max={2} step={0.1}
              value={form.temperature ?? 0.7}
              onChange={e => setForm(f => ({ ...f, temperature: parseFloat(e.target.value) || 0.7 }))}
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Max Tokens</label>
            <Input
              type="number" min={1} max={100000}
              value={form.max_tokens ?? 2048}
              onChange={e => setForm(f => ({ ...f, max_tokens: parseInt(e.target.value) || 2048 }))}
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Timeout (seconds)</label>
            <Input
              type="number" min={1} max={300}
              value={form.timeout_seconds ?? 60}
              onChange={e => setForm(f => ({ ...f, timeout_seconds: parseInt(e.target.value) || 60 }))}
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Max Retries</label>
            <Input
              type="number" min={0} max={10}
              value={form.max_retries ?? 3}
              onChange={e => setForm(f => ({ ...f, max_retries: parseInt(e.target.value) || 3 }))}
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Retry Delay (seconds)</label>
            <Input
              type="number" min={0} max={60} step={0.5}
              value={form.retry_delay_seconds ?? 1}
              onChange={e => setForm(f => ({ ...f, retry_delay_seconds: parseFloat(e.target.value) || 1 }))}
            />
          </div>
          <div className="flex items-end pb-2">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.streaming_enabled ?? true}
                onChange={e => setForm(f => ({ ...f, streaming_enabled: e.target.checked }))}
                className="rounded border-glass-border bg-dark-800"
              />
              Streaming Enabled
            </label>
          </div>
        </div>

        {saved && (
          <div className="flex items-center gap-1 text-sm text-success">
            <CheckCircle2 className="h-4 w-4" />
            Configuration saved successfully
          </div>
        )}

        <div className="flex flex-wrap gap-2 pt-2">
          <Button onClick={handleSave} disabled={updateConfig.isPending}>
            {updateConfig.isPending ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Save className="h-4 w-4 mr-1" />}
            Save Configuration
          </Button>
          <Button variant="outline" onClick={handleReset}>
            <RotateCcw className="h-4 w-4 mr-1" />
            Reset to Defaults
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
