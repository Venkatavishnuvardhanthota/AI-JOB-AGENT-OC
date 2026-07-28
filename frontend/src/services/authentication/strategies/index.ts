import type { AuthenticationStrategy } from './base-strategy'
import { OAuthStrategy } from './oauth-strategy'
import { UsernamePasswordStrategy } from './username-password-strategy'
import { CookiesStrategy } from './cookies-strategy'
import { SessionTokenStrategy } from './session-token-strategy'
import { BrowserSessionStrategy } from './browser-session-strategy'
import { ApiKeyStrategy } from './api-key-strategy'
import { AnonymousStrategy } from './anonymous-strategy'

export type { AuthenticationStrategy } from './base-strategy'
export { getDescriptor, createSessionRecord } from './base-strategy'
export { OAuthStrategy } from './oauth-strategy'
export { UsernamePasswordStrategy } from './username-password-strategy'
export { CookiesStrategy } from './cookies-strategy'
export { SessionTokenStrategy } from './session-token-strategy'
export { BrowserSessionStrategy } from './browser-session-strategy'
export { ApiKeyStrategy } from './api-key-strategy'
export { AnonymousStrategy } from './anonymous-strategy'

const DEFAULT_STRATEGIES: AuthenticationStrategy[] = [
  new OAuthStrategy(),
  new UsernamePasswordStrategy(),
  new CookiesStrategy(),
  new SessionTokenStrategy(),
  new BrowserSessionStrategy(),
  new ApiKeyStrategy(),
  new AnonymousStrategy(),
]

export function getDefaultStrategies(): AuthenticationStrategy[] {
  return DEFAULT_STRATEGIES.map(s => s)
}
