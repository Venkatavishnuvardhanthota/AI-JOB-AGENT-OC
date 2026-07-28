import type { BrowserAttachment } from './types'
import { authSessionManager } from './auth-session-manager'
import { emitAuthLog } from './observability-integration'

export const authBrowserIntegration = {
  attachSession(authSessionId: string, providerId: string, browserId: string): BrowserAttachment {
    const authSession = authSessionManager.get(providerId, authSessionId)
    if (!authSession) throw new Error(`Auth session ${authSessionId} not found for provider ${providerId}`)

    authSessionManager.update(providerId, authSessionId, {
      metadata: { ...authSession.metadata, browserId, attachedAt: new Date().toISOString() },
    })

    const attachment: BrowserAttachment = {
      browserId,
      sessionId: authSessionId,
      attachedAt: new Date().toISOString(),
      cookiesImported: false,
      cookiesExported: false,
      profileReused: false,
    }

    emitAuthLog(providerId, 'info', `Browser session ${browserId} attached to auth session ${authSessionId}`, { browserId, authSessionId })
    return attachment
  },

  detachSession(authSessionId: string, providerId: string): void {
    const authSession = authSessionManager.get(providerId, authSessionId)
    if (authSession) {
      const { browserId, ...rest } = authSession.metadata
      authSessionManager.update(providerId, authSessionId, { metadata: { ...rest, detachedAt: new Date().toISOString() } })
      emitAuthLog(providerId, 'info', `Browser detached from auth session ${authSessionId}`, { authSessionId })
    }
  },

  reuseProfile(authSessionId: string, providerId: string, browserId: string): BrowserAttachment {
    const attachment = this.attachSession(authSessionId, providerId, browserId)
    authSessionManager.update(providerId, authSessionId, {
      metadata: { ...authSessionManager.get(providerId, authSessionId)?.metadata, profileReused: true },
    })
    emitAuthLog(providerId, 'info', `Browser profile reused for auth session ${authSessionId}`, { browserId, authSessionId })
    return { ...attachment, profileReused: true }
  },

  importCookies(authSessionId: string, providerId: string, cookies: Record<string, unknown>[]): void {
    const session = authSessionManager.get(providerId, authSessionId)
    if (session) {
      authSessionManager.update(providerId, authSessionId, {
        sessionData: { ...session.sessionData, importedCookies: cookies },
      })
      emitAuthLog(providerId, 'info', `Cookies imported for auth session ${authSessionId}`, { cookieCount: cookies.length })
    }
  },

  exportCookies(providerId: string, authSessionId: string): Record<string, unknown>[] {
    const session = authSessionManager.get(providerId, authSessionId)
    const cookies = (session?.sessionData?.importedCookies as Record<string, unknown>[]) ?? []
    emitAuthLog(providerId, 'info', `Cookies exported from auth session ${authSessionId}`, { cookieCount: cookies.length })
    return cookies
  },
}
