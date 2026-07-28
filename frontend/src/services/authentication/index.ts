export { authenticationManager } from './authentication-manager'
export { authenticationRegistry } from './registry'
export { authSessionManager } from './auth-session-manager'
export { authConfiguration } from './configuration'
export { authEventEmitter } from './event-emitter'
export { validationEngine } from './validation-engine'
export { credentialStorage } from './storage'
export { getAuthAnalytics, recordAuthMetric, recordAuthDuration, emitAuthLog } from './observability-integration'
export { authBrowserIntegration } from './browser-integration'
export { CredentialBundle } from './credentials'
export { AuthLifecycle } from './lifecycle'

export type { AuthenticationStrategy } from './strategies/base-strategy'
export {
  getDefaultStrategies,
  getDescriptor,
  createSessionRecord,
  OAuthStrategy,
  UsernamePasswordStrategy,
  CookiesStrategy,
  SessionTokenStrategy,
  BrowserSessionStrategy,
  ApiKeyStrategy,
  AnonymousStrategy,
} from './strategies'

export type * from './types'
