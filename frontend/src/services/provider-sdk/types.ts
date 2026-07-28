export type CapabilityId =
  | 'search'
  | 'apply'
  | 'authentication'
  | 'browser_automation'
  | 'api'
  | 'resume_upload'
  | 'cover_letter_upload'
  | 'questionnaire'
  | 'tracking'
  | 'salary_range'
  | 'company_profile'
  | 'filter_by_location'
  | 'filter_by_salary'
  | 'filter_by_experience'
  | 'filter_by_type'
  | 'easy_apply'

export type AuthMethodType = 'oauth' | 'cookies' | 'credentials' | 'session_token' | 'browser_session'

export type ProviderStatus = 'initializing' | 'active' | 'error' | 'degraded' | 'disabled'

export type LifecycleState = 'created' | 'initialized' | 'authenticated' | 'active' | 'error' | 'cleaned_up'

export interface ProviderMetadata {
  id: string
  name: string
  version: string
  description: string
  author?: string
  homepage?: string
  capabilities: CapabilityId[]
  authMethods: AuthMethodType[]
  configSchema?: Record<string, unknown>
}

export interface ProviderContext {
  correlationId: string
  requestId: string
  providerId: string
  config: Record<string, unknown>
  authState?: unknown
  sessionId?: string
  userId?: string
  startTime: number
  metadata: Record<string, unknown>
}

export interface PipelineStage {
  name: string
  execute<T>(input: T, context: ProviderContext): Promise<T>
}

export interface PipelineResult<T> {
  success: boolean
  data?: T
  error?: Error
  duration: number
  attempts: number
  cached: boolean
}

export interface CacheEntry<T> {
  data: T
  expiresAt: number
  createdAt: string
}

export interface AuthCredentials {
  username?: string
  password?: string
  token?: string
  apiKey?: string
  clientId?: string
  clientSecret?: string
  sessionCookie?: string
  additionalFields?: Record<string, string>
}

export interface AuthSession {
  method: AuthMethodType
  authenticated: boolean
  expiresAt: string | null
  sessionData: Record<string, unknown>
}

export interface ProviderCapabilityDescriptor {
  id: CapabilityId
  name: string
  description: string
  required?: boolean
}

export interface RetryConfig {
  maxRetries: number
  baseDelayMs: number
  maxDelayMs: number
  retryableErrors: string[]
}

export interface CacheConfig {
  enabled: boolean
  ttlMs: number
  maxEntries: number
}

export interface PipelineConfig {
  retry: RetryConfig
  cache: CacheConfig
  timeoutMs: number
  validateResponse: boolean
}

export interface ProviderConfiguration {
  id: string
  enabled: boolean
  priority: number
  config: Record<string, unknown>
  pipeline: PipelineConfig
  credentials?: AuthCredentials
  metadata: ProviderMetadata
}

export interface ProviderHealthCheckResult {
  status: 'healthy' | 'degraded' | 'unhealthy'
  latency: number
  lastCheck: string
  message?: string
  details?: Record<string, unknown>
}

export interface NormalizedResponse<T> {
  data: T[]
  total: number
  hasMore: boolean
  cursor?: string
}

export interface SdkEventMap {
  'provider:registered': { providerId: string; metadata: ProviderMetadata }
  'provider:unregistered': { providerId: string }
  'provider:initialized': { providerId: string; duration: number }
  'provider:error': { providerId: string; error: Error; context: ProviderContext }
  'provider:health': { providerId: string; result: ProviderHealthCheckResult }
  'provider:lifecycle': { providerId: string; from: LifecycleState; to: LifecycleState }
}
