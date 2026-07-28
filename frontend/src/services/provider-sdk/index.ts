export { ProviderLifecycle } from './provider-lifecycle'
export { requestPipeline } from './request-pipeline'
export { responseNormalizer } from './response-normalizer'
export { capabilitySystem } from './capability-system'
export { providerRegistry } from './provider-registry'
export { createProvider, createAndRegisterProvider } from './provider-factory'
export { createAuthProvider } from './auth-abstraction'
export {
  createObservabilityContext,
  emitProviderMetrics,
  emitProviderLog,
  emitProviderAlert,
  trackProviderHealth,
  wrapWithObservability,
  initializeProviderObservability,
  trackProviderCapabilityUsage,
} from './observability-integration'

export {
  ProviderError,
  AuthenticationError,
  RateLimitError,
  SessionExpiredError,
  ProviderUnavailableError,
  SearchError,
  ApplicationError,
  ValidationError,
  TimeoutError,
  NotImplementedError,
  isProviderError,
  isRecoverableError,
  getErrorCode,
} from './errors'

export type * from './types'
export type { AuthProvider } from './auth-abstraction'
export type { ProviderImplementation, CreatedProvider } from './provider-factory'
