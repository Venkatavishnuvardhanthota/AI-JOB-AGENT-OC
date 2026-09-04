import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/components/ui/toast'
import { ProviderCapabilities } from '@/components/ai/ProviderCapabilities'
import {
  useTestAIConnection,
  useAIModels,
  useUpdateProviderConfig,
  useDeleteProviderConfig,
  useUpdateAIConfig,
} from '@/api/hooks'
import type { AIProvider } from '@/types'
import {
  X,
  Save,
  Loader2,
  Activity,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Eye,
  EyeOff,
  Shield,
  Trash2,
} from 'lucide-react'

interface ProviderConfigFormProps {
  provider: AIProvider | null
  open: boolean
  onClose: () => void
}

export function ProviderConfigForm({ provider, open, onClose }: ProviderConfigFormProps) {
  const { addToast } = useToast()
  const testMutation = useTestAIConnection()
  const saveMutation = useUpdateProviderConfig()
  const deleteMutation = useDeleteProviderConfig()
  const updateConfigMutation = useUpdateAIConfig()
  const { data: models, refetch: refetchModels } = useAIModels(provider?.name)
  const [testResult, setTestResult] = useState<{ healthy: boolean; latency_ms?: number; error?: string } | null>(null)
  const [showApiKey, setShowApiKey] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [selectedModel, setSelectedModel] = useState('')

  const [form, setForm] = useState({
    apiKey: '',
    baseUrl: '',
    defaultModel: '',
    temperature: 0.7,
    maxTokens: 2048,
    timeout: 60,
    retryCount: 3,
    retryDelay: 1,
    streamingEnabled: true,
    fallbackEnabled: false,
    enabled: true,
    isDefault: false,
  })

  useEffect(() => {
    if (provider) {
      const saved = provider.saved_config
      setForm({
        apiKey: '',
        baseUrl: saved?.base_url || '',
        defaultModel: saved?.default_model || '',
        temperature: saved?.temperature ?? 0.7,
        maxTokens: saved?.max_tokens ?? 2048,
        timeout: saved?.timeout_seconds ?? 60,
        retryCount: saved?.max_retries ?? 3,
        retryDelay: saved?.retry_delay_seconds ?? 1,
        streamingEnabled: saved?.streaming_enabled ?? true,
        fallbackEnabled: false,
        enabled: saved?.is_enabled ?? true,
        isDefault: provider.is_default,
      })
      setTestResult(null)
      setSelectedModel('')
    }
  }, [provider])

  if (!open || !provider) return null

  const handleTest = async () => {
    setTestResult(null)
    testMutation.mutate(provider.name, {
      onSuccess: (data) => {
        setTestResult({ healthy: data.healthy, latency_ms: data.latency_ms, error: data.error })
      },
      onError: (err: Error) => {
        setTestResult({ healthy: false, error: err.message })
        addToast(`Test failed: ${err.message}`, 'error')
      },
    })
  }

  const handleRefreshModels = async () => {
    setRefreshing(true)
    try {
      await refetchModels()
      addToast('Models refreshed', 'success')
    } catch {
      addToast('Failed to refresh models', 'error')
    } finally {
      setRefreshing(false)
    }
  }

  const handleDeleteKey = () => {
    deleteMutation.mutate(provider.name, {
      onSuccess: () => {
        setForm(f => ({ ...f, apiKey: '' }))
        addToast(`${provider.display_name} saved API key cleared`, 'success')
      },
      onError: (err: Error) => {
        addToast(`Failed to clear API key: ${err.message}`, 'error')
      },
    })
  }

  const handleSave = () => {
    saveMutation.mutate(
      {
        provider: provider.name,
        data: {
          api_key: form.apiKey || undefined,
          base_url: form.baseUrl || undefined,
          default_model: selectedModel || form.defaultModel || undefined,
          is_enabled: form.enabled,
          temperature: form.temperature,
          max_tokens: form.maxTokens,
          timeout_seconds: form.timeout,
          max_retries: form.retryCount,
          retry_delay_seconds: form.retryDelay,
          streaming_enabled: form.streamingEnabled,
        },
      },
      {
        onSuccess: () => {
          addToast(`${provider.display_name} configuration saved`, 'success')
          if (form.isDefault && !provider.is_default) {
            updateConfigMutation.mutate(
              { default_provider: provider.name, default_model: selectedModel || form.defaultModel || undefined },
              { onSuccess: () => addToast(`${provider.display_name} set as default provider`, 'success') },
            )
          }
          onClose()
        },
        onError: (err: Error) => {
          addToast(`Failed to save configuration: ${err.message}`, 'error')
        },
      },
    )
  }

  const selectedModelValue = selectedModel || form.defaultModel || ''

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-16" onClick={onClose}>
      <div className="absolute inset-0 bg-black/50" />
      <div
        className="relative z-10 w-full max-w-lg rounded-xl border border-glass-border bg-dark-900 shadow-xl max-h-[80vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-glass-border">
          <div>
            <h3 className="text-lg font-semibold">{provider.display_name}</h3>
            <p className="text-xs text-muted-foreground">{provider.name}</p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}><X className="h-4 w-4" /></Button>
        </div>

        <div className="p-4 space-y-4">
          <div className="flex flex-wrap gap-1">
            {provider.configured && <Badge variant="success">Configured</Badge>}
            {provider.is_default && <Badge variant="default">Default</Badge>}
            {provider.is_available ? <Badge variant="success">Available</Badge> : <Badge variant="warning">Unavailable</Badge>}
            {provider.saved_config?.api_key_set && <Badge variant="outline">API key saved</Badge>}
          </div>

          {provider.capabilities && (
            <div>
              <p className="text-xs text-muted-foreground mb-1">Capabilities</p>
              <ProviderCapabilities capabilities={provider.capabilities} />
            </div>
          )}

          <div>
            <p className="text-xs text-muted-foreground mb-1">Available Models ({models?.length || 0})</p>
            <div className="flex gap-2">
              <Select
                value={selectedModelValue}
                onChange={e => setSelectedModel(e.target.value)}
                className="flex-1"
              >
                <option value="">{form.defaultModel || 'Select a model...'}</option>
                {(models || []).map((m: any) => (
                  <option key={m.id} value={m.id}>{m.name || m.id}</option>
                ))}
              </Select>
              <Button size="sm" variant="outline" onClick={handleRefreshModels} disabled={refreshing}>
                <RefreshCw className={`h-3 w-3 ${refreshing ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>

          <div className="space-y-3 border-t border-glass-border pt-3">
            <p className="text-sm font-medium flex items-center gap-1">
              <Shield className="h-4 w-4 text-primary" />
              Authentication
            </p>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">API Key</label>
              <div className="flex gap-1">
                <Input
                  type={showApiKey ? 'text' : 'password'}
                  value={form.apiKey}
                  onChange={e => setForm(f => ({ ...f, apiKey: e.target.value }))}
                  placeholder={provider.saved_config?.api_key_set ? 'Saved key (enter to replace)' : 'Enter API key...'}
                  className="flex-1"
                />
                <Button variant="outline" size="icon" onClick={() => setShowApiKey(!showApiKey)} title={showApiKey ? 'Hide' : 'Show'}>
                  {showApiKey ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                </Button>
                {provider.saved_config?.api_key_set && (
                  <Button variant="outline" size="icon" onClick={handleDeleteKey} title="Clear saved API key" disabled={deleteMutation.isPending}>
                    <Trash2 className="h-3 w-3 text-error" />
                  </Button>
                )}
              </div>
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Base URL</label>
              <Input
                value={form.baseUrl}
                onChange={e => setForm(f => ({ ...f, baseUrl: e.target.value }))}
                placeholder="https://api.example.com/v1"
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Default Model</label>
              <Input
                value={form.defaultModel}
                onChange={e => setForm(f => ({ ...f, defaultModel: e.target.value }))}
                placeholder="e.g. gpt-4o"
              />
            </div>
          </div>

          <div className="space-y-3 border-t border-glass-border pt-3">
            <p className="text-sm font-medium">Parameters</p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Temperature</label>
                <Input
                  type="number"
                  min={0} max={2} step={0.1}
                  value={form.temperature}
                  onChange={e => setForm(f => ({ ...f, temperature: parseFloat(e.target.value) || 0.7 }))}
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Max Tokens</label>
                <Input
                  type="number"
                  min={1} max={100000}
                  value={form.maxTokens}
                  onChange={e => setForm(f => ({ ...f, maxTokens: parseInt(e.target.value) || 2048 }))}
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Timeout (s)</label>
                <Input
                  type="number"
                  min={1} max={300}
                  value={form.timeout}
                  onChange={e => setForm(f => ({ ...f, timeout: parseInt(e.target.value) || 60 }))}
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Retry Count</label>
                <Input
                  type="number"
                  min={0} max={10}
                  value={form.retryCount}
                  onChange={e => setForm(f => ({ ...f, retryCount: parseInt(e.target.value) || 3 }))}
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Retry Delay (s)</label>
                <Input
                  type="number"
                  min={0} max={60}
                  value={form.retryDelay}
                  onChange={e => setForm(f => ({ ...f, retryDelay: parseFloat(e.target.value) || 1 }))}
                />
              </div>
            </div>
          </div>

          <div className="space-y-2 border-t border-glass-border pt-3">
            <p className="text-sm font-medium">Options</p>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.streamingEnabled}
                onChange={e => setForm(f => ({ ...f, streamingEnabled: e.target.checked }))}
                className="rounded border-glass-border bg-dark-800"
              />
              Streaming Enabled
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.enabled}
                onChange={e => setForm(f => ({ ...f, enabled: e.target.checked }))}
                className="rounded border-glass-border bg-dark-800"
              />
              Provider Enabled
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.isDefault}
                onChange={e => setForm(f => ({ ...f, isDefault: e.target.checked }))}
                className="rounded border-glass-border bg-dark-800"
              />
              Set as Default Provider
            </label>
          </div>

          {testResult && (
            <div className={`text-sm flex items-center gap-1 p-2 rounded ${testResult.healthy ? 'bg-success/10 text-success' : 'bg-error/10 text-error'}`}>
              {testResult.healthy ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
              {testResult.healthy
                ? `Connection successful (${testResult.latency_ms?.toFixed(0)}ms)`
                : testResult.error || 'Connection failed'}
            </div>
          )}
        </div>

        <div className="flex items-center justify-between p-4 border-t border-glass-border">
          <Button variant="outline" onClick={handleTest} disabled={testMutation.isPending}>
            {testMutation.isPending ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Activity className="h-4 w-4 mr-1" />}
            Test Connection
          </Button>
          <div className="flex gap-2">
            <Button variant="ghost" onClick={onClose}>Cancel</Button>
            <Button onClick={handleSave} disabled={saveMutation.isPending || updateConfigMutation.isPending}>
              {saveMutation.isPending ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Save className="h-4 w-4 mr-1" />}
              Save Configuration
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
