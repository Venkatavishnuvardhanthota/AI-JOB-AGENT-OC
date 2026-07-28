import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { browserFactory } from '@/services/browser/browser-factory'
import { browserManager } from '@/services/browser/browser-manager'
import type { BrowserState } from '@/services/browser/types'
import { Globe, Play, StopCircle, Trash2 } from 'lucide-react'

export function BrowserList() {
  const [browsers, setBrowsers] = useState<BrowserState[]>([])

  const refresh = () => setBrowsers(browserFactory.listAll())

  useEffect(() => { refresh() }, [])

  const handleLaunch = async () => {
    await browserManager.launch('chromium', { headless: false })
    refresh()
  }

  const handleClose = async (id: string) => {
    await browserManager.close(id)
    refresh()
  }

  const handleRemove = (id: string) => {
    browserFactory.remove(id)
    refresh()
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">Browser Instances</h3>
        <Button size="sm" onClick={handleLaunch}>
          <Play className="h-4 w-4 mr-1" /> Launch Browser
        </Button>
      </div>
      {browsers.length === 0 && (
        <p className="text-sm text-muted-foreground py-8 text-center">No browser instances. Click "Launch Browser" to start one.</p>
      )}
      {browsers.map(b => (
        <Card key={b.id} className="p-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Globe className="h-5 w-5 text-muted-foreground" />
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">{b.provider}</span>
                <Badge variant={b.status === 'running' ? 'success' : b.status === 'error' ? 'destructive' : 'secondary'}>
                  {b.status}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground">Pages: {b.metrics.pageLoads} | Actions: {b.metrics.actions} | Errors: {b.metrics.errors}</p>
            </div>
          </div>
          <div className="flex gap-1">
            {b.status === 'running' && (
              <Button variant="ghost" size="sm" onClick={() => handleClose(b.id)}><StopCircle className="h-4 w-4" /></Button>
            )}
            <Button variant="ghost" size="sm" onClick={() => handleRemove(b.id)}><Trash2 className="h-4 w-4" /></Button>
          </div>
        </Card>
      ))}
    </div>
  )
}
