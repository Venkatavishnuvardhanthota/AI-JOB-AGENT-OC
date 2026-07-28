import type { AuthMethodType, AuthCredentials, AuthSession } from './types'
import { AuthenticationError } from './errors'

interface AuthProvider {
  method: AuthMethodType
  authenticate(credentials: AuthCredentials): Promise<AuthSession>
  validateSession(session: AuthSession): Promise<boolean>
  refreshSession(session: AuthSession): Promise<AuthSession>
  logout(session: AuthSession): Promise<void>
}

class OAuthProvider implements AuthProvider {
  readonly method: AuthMethodType = 'oauth'

  async authenticate(credentials: AuthCredentials): Promise<AuthSession> {
    if (!credentials.clientId || !credentials.clientSecret) {
      throw new AuthenticationError('OAuth requires clientId and clientSecret')
    }
    return {
      method: 'oauth',
      authenticated: true,
      expiresAt: new Date(Date.now() + 3600000).toISOString(),
      sessionData: { accessToken: credentials.token, clientId: credentials.clientId },
    }
  }

  async validateSession(session: AuthSession): Promise<boolean> {
    if (!session.authenticated) return false
    if (session.expiresAt && new Date(session.expiresAt).getTime() < Date.now()) return false
    return true
  }

  async refreshSession(_session: AuthSession): Promise<AuthSession> {
    return {
      method: 'oauth',
      authenticated: true,
      expiresAt: new Date(Date.now() + 3600000).toISOString(),
      sessionData: { ..._session.sessionData, refreshed: true },
    }
  }

  async logout(_session: AuthSession): Promise<void> {
    return undefined
  }
}

class CookieAuthProvider implements AuthProvider {
  readonly method: AuthMethodType = 'cookies'

  async authenticate(credentials: AuthCredentials): Promise<AuthSession> {
    if (!credentials.sessionCookie) {
      throw new AuthenticationError('Cookie auth requires sessionCookie')
    }
    return {
      method: 'cookies',
      authenticated: true,
      expiresAt: new Date(Date.now() + 86400000).toISOString(),
      sessionData: { cookie: credentials.sessionCookie },
    }
  }

  async validateSession(session: AuthSession): Promise<boolean> {
    if (!session.authenticated) return false
    if (session.expiresAt && new Date(session.expiresAt).getTime() < Date.now()) return false
    return true
  }

  async refreshSession(session: AuthSession): Promise<AuthSession> {
    return { ...session, expiresAt: new Date(Date.now() + 86400000).toISOString() }
  }

  async logout(_session: AuthSession): Promise<void> {
    return undefined
  }
}

class CredentialsAuthProvider implements AuthProvider {
  readonly method: AuthMethodType = 'credentials'

  async authenticate(credentials: AuthCredentials): Promise<AuthSession> {
    if (!credentials.username || !credentials.password) {
      throw new AuthenticationError('Credentials auth requires username and password')
    }
    return {
      method: 'credentials',
      authenticated: true,
      expiresAt: new Date(Date.now() + 43200000).toISOString(),
      sessionData: { username: credentials.username },
    }
  }

  async validateSession(session: AuthSession): Promise<boolean> {
    if (!session.authenticated) return false
    if (session.expiresAt && new Date(session.expiresAt).getTime() < Date.now()) return false
    return true
  }

  async refreshSession(session: AuthSession): Promise<AuthSession> {
    return { ...session, expiresAt: new Date(Date.now() + 43200000).toISOString() }
  }

  async logout(_session: AuthSession): Promise<void> {
    return undefined
  }
}

class SessionTokenAuthProvider implements AuthProvider {
  readonly method: AuthMethodType = 'session_token'

  async authenticate(credentials: AuthCredentials): Promise<AuthSession> {
    if (!credentials.token) {
      throw new AuthenticationError('Session token auth requires token')
    }
    return {
      method: 'session_token',
      authenticated: true,
      expiresAt: new Date(Date.now() + 7200000).toISOString(),
      sessionData: { token: credentials.token },
    }
  }

  async validateSession(session: AuthSession): Promise<boolean> {
    if (!session.authenticated) return false
    if (session.expiresAt && new Date(session.expiresAt).getTime() < Date.now()) return false
    return true
  }

  async refreshSession(session: AuthSession): Promise<AuthSession> {
    return { ...session, expiresAt: new Date(Date.now() + 7200000).toISOString() }
  }

  async logout(_session: AuthSession): Promise<void> {
    return undefined
  }
}

class BrowserSessionAuthProvider implements AuthProvider {
  readonly method: AuthMethodType = 'browser_session'

  async authenticate(credentials: AuthCredentials): Promise<AuthSession> {
    return {
      method: 'browser_session',
      authenticated: true,
      expiresAt: new Date(Date.now() + 1800000).toISOString(),
      sessionData: { ...credentials.additionalFields },
    }
  }

  async validateSession(session: AuthSession): Promise<boolean> {
    if (!session.authenticated) return false
    if (session.expiresAt && new Date(session.expiresAt).getTime() < Date.now()) return false
    return true
  }

  async refreshSession(session: AuthSession): Promise<AuthSession> {
    return { ...session, expiresAt: new Date(Date.now() + 1800000).toISOString() }
  }

  async logout(_session: AuthSession): Promise<void> {
    return undefined
  }
}

const PROVIDER_MAP: Record<AuthMethodType, () => AuthProvider> = {
  oauth: () => new OAuthProvider(),
  cookies: () => new CookieAuthProvider(),
  credentials: () => new CredentialsAuthProvider(),
  session_token: () => new SessionTokenAuthProvider(),
  browser_session: () => new BrowserSessionAuthProvider(),
}

export function createAuthProvider(method: AuthMethodType): AuthProvider {
  const factory = PROVIDER_MAP[method]
  if (!factory) throw new AuthenticationError(`Unsupported auth method: ${method}`)
  return factory()
}

export type { AuthProvider }
