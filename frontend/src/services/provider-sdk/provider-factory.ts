import type { ProviderMetadata, ProviderContext, ProviderConfiguration, ProviderHealthCheckResult, CapabilityId, AuthCredentials, AuthMethodType, PipelineConfig } from './types'
import type { SearchParams, SearchResult, Job, ProviderId, RawJob } from '../discovery/types'
import { ProviderLifecycle } from './provider-lifecycle'
import { requestPipeline } from './request-pipeline'
import { responseNormalizer } from './response-normalizer'
import { wrapWithObservability, initializeProviderObservability, trackProviderCapabilityUsage, emitProviderLog } from './observability-integration'
import { NotImplementedError } from './errors'
import { capabilitySystem } from './capability-system'
import { providerRegistry } from './provider-registry'
import { normalizeJob, normalizeJobs } from '../discovery/normalization'

export interface ProviderImplementation {
  metadata: ProviderMetadata
  search?: (params: SearchParams, ctx: ProviderContext) => Promise<{ data: RawJob[]; total?: number; hasMore?: boolean; cursor?: string }>
  fetchJob?: (externalId: string, ctx: ProviderContext) => Promise<RawJob | null>
  apply?: (jobId: string, applicationData: Record<string, unknown>, ctx: ProviderContext) => Promise<{ success: boolean; applicationId?: string; message?: string }>
  healthCheck?: (ctx: ProviderContext) => Promise<ProviderHealthCheckResult>
  authenticate?: (credentials: AuthCredentials, ctx: ProviderContext) => Promise<void>
  validateSession?: (ctx: ProviderContext) => Promise<boolean>
  logout?: (ctx: ProviderContext) => Promise<void>
  cleanup?: (ctx: ProviderContext) => Promise<void>
  configuration?: Partial<ProviderConfiguration>
}

export interface CreatedProvider {
  metadata: ProviderMetadata
  lifecycle: ProviderLifecycle
  search(params: SearchParams): Promise<SearchResult>
  health(): Promise<ProviderHealthCheckResult>
  fetchJob?(externalId: string): Promise<Job | null>
  apply?(jobId: string, applicationData: Record<string, unknown>): Promise<{ success: boolean; applicationId?: string; message?: string }>
  authenticate?(credentials: AuthCredentials): Promise<void>
  logout?(): Promise<void>
  cleanup?(): Promise<void>
  getConfig(): ProviderConfiguration | undefined
  updateConfig(updates: Partial<ProviderConfiguration>): void
}

function createSourceUrl(providerId: string, keywords: string): string {
  return `https://${providerId}.com/search?q=${encodeURIComponent(keywords)}`
}

function buildDefaultConfig(metadata: ProviderMetadata): ProviderConfiguration {
  return {
    id: metadata.id,
    enabled: true,
    priority: 100,
    config: {},
    pipeline: {
      retry: { maxRetries: 3, baseDelayMs: 1000, maxDelayMs: 10000, retryableErrors: ['RATE_LIMIT_ERROR', 'TIMEOUT_ERROR', 'PROVIDER_UNAVAILABLE_ERROR'] },
      cache: { enabled: true, ttlMs: 300000, maxEntries: 500 },
      timeoutMs: 30000,
      validateResponse: true,
    },
    metadata,
  }
}

export function createProvider(implementation: ProviderImplementation): CreatedProvider {
  const metadata = implementation.metadata
  const lifecycle = new ProviderLifecycle(metadata.id)
  const localConfig: ProviderConfiguration = implementation.configuration
    ? { ...buildDefaultConfig(metadata), ...implementation.configuration }
    : buildDefaultConfig(metadata)

  initializeProviderObservability(metadata)

  const createdProvider: CreatedProvider = {
    metadata,
    lifecycle,

    async search(params: SearchParams): Promise<SearchResult> {
      const startTime = Date.now()

      if (!implementation.search) {
        return { jobs: [], totalResults: 0, page: params.page, pageSize: params.pageSize, hasMore: false, provider: metadata.id as ProviderId, duration: 0, error: null }
      }

      try {
        const result = await wrapWithObservability(metadata.id, 'search', async (ctx: ProviderContext) => {
          const pipelineResult = await requestPipeline.execute(
            'search',
            params,
            async () => implementation.search!(params, ctx),
            ctx,
            implementation.configuration?.pipeline
          )

          if (!pipelineResult.success || !pipelineResult.data) {
            throw pipelineResult.error ?? new Error('Search returned no data')
          }

          return pipelineResult.data as { data: RawJob[]; total?: number; hasMore?: boolean; cursor?: string }
        })

        const sourceUrl = createSourceUrl(metadata.id, params.keywords)
        const jobs = responseNormalizer.normalizeMany(result.data, metadata.id, sourceUrl)
        const duration = Date.now() - startTime

        trackProviderCapabilityUsage(metadata.id, 'search', duration, true)

        return {
          jobs: result.data,
          totalResults: result.total ?? result.data.length,
          page: params.page,
          pageSize: params.pageSize,
          hasMore: result.hasMore ?? false,
          provider: metadata.id as ProviderId,
          duration,
          error: null,
        }
      } catch (error) {
        const duration = Date.now() - startTime
        trackProviderCapabilityUsage(metadata.id, 'search', duration, false)
        return {
          jobs: [],
          totalResults: 0,
          page: params.page,
          pageSize: params.pageSize,
          hasMore: false,
          provider: metadata.id as ProviderId,
          duration,
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },

    async health(): Promise<ProviderHealthCheckResult> {
      if (!implementation.healthCheck) {
        return { status: 'healthy', latency: 0, lastCheck: new Date().toISOString() }
      }

      try {
        return await wrapWithObservability(metadata.id, 'healthCheck', async (ctx) => {
          const result = await implementation.healthCheck!(ctx)
          return result
        })
      } catch {
        return { status: 'unhealthy', latency: 0, lastCheck: new Date().toISOString(), message: 'Health check threw exception' }
      }
    },

    async fetchJob(externalId: string): Promise<Job | null> {
      if (!implementation.fetchJob) throw new NotImplementedError('fetchJob', metadata.id)
      return wrapWithObservability(metadata.id, 'fetchJob', async (ctx) => {
        const raw = await implementation.fetchJob!(externalId, ctx)
        if (!raw) return null
        const sourceUrl = createSourceUrl(metadata.id, externalId)
        return normalizeJob(raw, metadata.id as ProviderId, sourceUrl)
      })
    },

    async apply(jobId: string, applicationData: Record<string, unknown>): Promise<{ success: boolean; applicationId?: string; message?: string }> {
      if (!implementation.apply) throw new NotImplementedError('apply', metadata.id)
      return wrapWithObservability(metadata.id, 'apply', async (ctx) => {
        return implementation.apply!(jobId, applicationData, ctx)
      })
    },

    async authenticate(credentials: AuthCredentials): Promise<void> {
      if (!implementation.authenticate) {
        await lifecycle.authenticate(credentials, metadata.authMethods)
        return
      }
      return wrapWithObservability(metadata.id, 'authenticate', async (ctx) => {
        await implementation.authenticate!(credentials, ctx)
        await lifecycle.authenticate(credentials, metadata.authMethods)
      })
    },

    async logout(): Promise<void> {
      if (!implementation.logout) {
        await lifecycle.logout()
        return
      }
      return wrapWithObservability(metadata.id, 'logout', async (ctx) => {
        await implementation.logout!(ctx)
        await lifecycle.logout()
      })
    },

    async cleanup(): Promise<void> {
      if (!implementation.cleanup) {
        await lifecycle.cleanup()
        return
      }
      return wrapWithObservability(metadata.id, 'cleanup', async (ctx) => {
        await implementation.cleanup!(ctx)
        await lifecycle.cleanup()
      })
    },

    getConfig(): ProviderConfiguration | undefined {
      const registered = providerRegistry.getConfig(metadata.id)
      return registered ?? localConfig
    },

    updateConfig(updates: Partial<ProviderConfiguration>): void {
      const registered = providerRegistry.getConfig(metadata.id)
      if (registered) {
        providerRegistry.updateConfig(metadata.id, updates)
      }
      Object.assign(localConfig, updates)
    },
  }

  return createdProvider
}

export function createAndRegisterProvider(implementation: ProviderImplementation): CreatedProvider {
  const provider = createProvider(implementation)
  providerRegistry.register(implementation.metadata, provider, implementation.configuration)
  return provider
}
