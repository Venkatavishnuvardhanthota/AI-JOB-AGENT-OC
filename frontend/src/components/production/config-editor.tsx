import { useEffect, useState } from 'react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { configService } from '@/services/production/config-service'
import type { AppConfig } from '@/services/production/config-service'
import { Settings, RefreshCw, CheckCircle, AlertTriangle } from 'lucide-react'

export function ConfigEditor() {
  const [config, setConfig] = useState<AppConfig>(configService.get())
  const [validation, setValidation] = useState(configService.validate())
  const [saved, setSaved] = useState(false)

  const refresh = () => {
    setConfig(configService.get())
    setValidation(configService.validate())
  }
  useEffect(() => { refresh() }, [])

  const handleToggleFeature = (key: string) => {
    configService.setFeatureFlag(key, !config.features[key])
    refresh()
    setSaved(true); setTimeout(() => setSaved(false), 2000)
  }

  const handleToggleProvider = (key: string) => {
    configService.toggleProvider(key, !config.providers[key])
    refresh()
    setSaved(true); setTimeout(() => setSaved(false), 2000)
  }

  const handleReset = () => {
    configService.reset()
    refresh()
    setSaved(true); setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">Configuration</h3>
        <div className="flex items-center gap-2">
          {saved && <Badge variant="success" className="text-[10px]"><CheckCircle className="h-3 w-3 mr-1" />Saved</Badge>}
          {!validation.valid && <Badge variant="destructive" className="text-[10px]"><AlertTriangle className="h-3 w-3 mr-1" />Invalid</Badge>}
          <Button variant="ghost" size="sm" className="h-6" onClick={handleReset}><RefreshCw className="h-3 w-3 mr-1" />Reset</Button>
        </div>
      </div>

      {!validation.valid && (
        <Card className="p-2 bg-red-500/10 border-red-500/20">
          <p className="text-xs text-red-400 font-medium">Validation Errors:</p>
          {validation.errors.map((e, i) => <p key={i} className="text-[10px] text-red-300">{e}</p>)}
        </Card>
      )}
      {validation.warnings.length > 0 && (
        <Card className="p-2 bg-yellow-500/10 border-yellow-500/20">
          <p className="text-xs text-yellow-400 font-medium">Warnings:</p>
          {validation.warnings.map((w, i) => <p key={i} className="text-[10px] text-yellow-300">{w}</p>)}
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <Card className="p-2 space-y-1">
          <h4 className="text-xs font-medium flex items-center gap-1"><Settings className="h-3 w-3" /> Environment</h4>
          <Badge variant={config.environment === 'production' ? 'destructive' : 'default'} className="text-[10px]">{config.environment}</Badge>
          <p className="text-[10px] text-muted-foreground">Version: {config.version}</p>
        </Card>

        <Card className="p-2 space-y-1">
          <h4 className="text-xs font-medium">Feature Flags</h4>
          {Object.entries(config.features).map(([key, enabled]) => (
            <div key={key} className="flex items-center justify-between py-0.5">
              <span className="text-[10px]">{key}</span>
              <button
                onClick={() => handleToggleFeature(key)}
                className={`text-[10px] px-1.5 py-0.5 rounded ${enabled ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}
              >
                {enabled ? 'ON' : 'OFF'}
              </button>
            </div>
          ))}
        </Card>

        <Card className="p-2 space-y-1">
          <h4 className="text-xs font-medium">Providers</h4>
          {Object.entries(config.providers).map(([key, enabled]) => (
            <div key={key} className="flex items-center justify-between py-0.5">
              <span className="text-[10px] capitalize">{key}</span>
              <button
                onClick={() => handleToggleProvider(key)}
                className={`text-[10px] px-1.5 py-0.5 rounded ${enabled ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}
              >
                {enabled ? 'ON' : 'OFF'}
              </button>
            </div>
          ))}
        </Card>

        <Card className="p-2 space-y-1">
          <h4 className="text-xs font-medium">Thresholds</h4>
          {Object.entries(config.thresholds).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between py-0.5">
              <span className="text-[10px]">{key}</span>
              <span className="text-[10px] text-muted-foreground">{value}</span>
            </div>
          ))}
        </Card>
      </div>
    </div>
  )
}
