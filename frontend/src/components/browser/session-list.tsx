import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { sessionManager } from '@/services/browser/session-manager'
import { browserFactory } from '@/services/browser/browser-factory'
import type { BrowserSession } from '@/services/browser/types'
import { Globe, X, Play, Pause } from 'lucide-react'

export function SessionList() {
  const [sessions, setSessions] = useState<{ browserId: string; session: BrowserSession }[]>([])

  const refresh = () => setSessions(sessionManager.getActiveSessions())

  useEffect(() => { refresh(); const iv = setInterval(refresh, 3000); return () => clearInterval(iv) }, [])

  const handleClose = (browserId: string, sessionId: string) => {
    sessionManager.close(browserId, sessionId)
    refresh()
  }

  const handlePause = (browserId: string, sessionId: string) => {
    sessionManager.pause(browserId, sessionId)
    refresh()
  }

  const handleResume = (browserId: string, sessionId: string) => {
    sessionManager.resume(browserId, sessionId)
    refresh()
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium">Active Sessions</h3>
      {sessions.length === 0 && (
        <p className="text-sm text-muted-foreground py-8 text-center">No active sessions.</p>
      )}
      {sessions.map(({ browserId, session }) => {
        const browser = browserFactory.get(browserId)
        return (
          <Card key={session.id} className="p-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Globe className="h-5 w-5 text-muted-foreground" />
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{session.url || 'No URL'}</span>
                  <Badge variant={session.status === 'active' ? 'success' : 'secondary'}>
                    {session.status}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground">
                  {browser?.provider ?? 'N/A'} | Tabs: {session.tabs.length}
                </p>
              </div>
            </div>
            <div className="flex gap-1">
              {session.status === 'active' ? (
                <Button variant="ghost" size="sm" onClick={() => handlePause(browserId, session.id)}>
                  <Pause className="h-4 w-4" />
                </Button>
              ) : session.status === 'paused' ? (
                <Button variant="ghost" size="sm" onClick={() => handleResume(browserId, session.id)}>
                  <Play className="h-4 w-4" />
                </Button>
              ) : null}
              <Button variant="ghost" size="sm" onClick={() => handleClose(browserId, session.id)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          </Card>
        )
      })}
    </div>
  )
}
