import { createAndRegisterProvider, type ProviderImplementation } from '../provider-sdk/provider-factory'
import type { SearchParams } from '../discovery/types'
import type { ProviderContext, CapabilityId } from '../provider-sdk/types'
import type { ATSProviderConfig, ATSJobRaw } from './ats-types'
import { normalizeATSJob } from './ats-types'
import { atsFetch } from './ats-http-client'
import { buildPaginationQuery, extractPaginationResult } from './ats-pagination'

function resolveEndpoint(template: string, config: ATSProviderConfig): string {
  return template
    .replace('{board_token}', config.boardToken ?? 'example')
    .replace('{company_id}', config.companyId ?? 'default')
    .replace('{list_id}', config.listId ?? 'default')
    .replace('{site}', config.site ?? 'default')
}

function buildSearchUrl(config: ATSProviderConfig, params: SearchParams, cursor?: string): string {
  const path = resolveEndpoint(config.endpoints.jobs, config)
  const query = buildPaginationQuery(config.pagination, { page: params.page, pageSize: params.pageSize }, cursor)
  if (params.keywords) query.q = params.keywords
  if (params.location) query.location = params.location
  if (params.employmentType) query.employment_type = params.employmentType
  if (params.remote) query.remote = params.remote
  return path + '?' + new URLSearchParams({ ...config.defaultParams, ...query }).toString()
}

export interface ATSProviderImplementation {
  config: ATSProviderConfig
  parseResponse(response: unknown, providerId: string): ATSJobRaw[]
  parseJobDetails?(job: ATSJobRaw, config: ATSProviderConfig): ATSJobRaw
  fetchJobs?(url: string, config: ATSProviderConfig, params: SearchParams): Promise<{ items: unknown[]; total: number; hasMore: boolean; cursor?: string }>
}

function createSearchImplementation(impl: ATSProviderImplementation) {
  return async (params: SearchParams, _ctx: ProviderContext) => {
    const config = impl.config
    let total = 0
    let hasMore = false
    let cursor: string | undefined

    if (impl.fetchJobs) {
      const url = buildSearchUrl(config, params)
      const result = await impl.fetchJobs(url, config, params)
      const items = result.items
      const parsed = impl.parseResponse(items, config.id)
      const jobs = parsed.map(j => normalizeATSJob(j, config.id))
      return { data: jobs, total: result.total, hasMore: result.hasMore, cursor: result.cursor }
    }

    const url = buildSearchUrl(config, params, cursor)
    const response = await atsFetch<unknown>(url, {
      baseUrl: config.baseUrl,
      providerId: config.id,
      rateLimitPerSecond: config.rateLimitPerSecond,
      timeoutMs: config.timeoutMs,
      headers: config.headers,
    })

    const paginationResult = extractPaginationResult<unknown>(response, config.pagination)
    total = paginationResult.total
    hasMore = paginationResult.hasMore
    cursor = paginationResult.cursor

    const items = paginationResult.items.length > 0
      ? paginationResult.items
      : Array.isArray(response) ? response : [response]

    const parsed = impl.parseResponse(items, config.id)
    const jobs = parsed.map(j => normalizeATSJob(j, config.id))
    return { data: jobs, total, hasMore, cursor }
  }
}

function createHealthCheckImplementation(impl: ATSProviderImplementation) {
  return async () => {
    try {
      const url = resolveEndpoint(impl.config.endpoints.jobs, impl.config)
      await atsFetch<unknown>(url, {
        baseUrl: impl.config.baseUrl,
        providerId: impl.config.id,
        timeoutMs: 5000,
      })
      return { status: 'healthy' as const, latency: 0, lastCheck: new Date().toISOString() }
    } catch {
      return { status: 'unhealthy' as const, latency: 0, lastCheck: new Date().toISOString(), message: `${impl.config.id} health check failed` }
    }
  }
}

export function createATSProvider(impl: ATSProviderImplementation): ReturnType<typeof createAndRegisterProvider> {
  const config = impl.config

  const providerImpl: ProviderImplementation = {
    metadata: {
      id: config.id,
      name: config.name,
      version: config.version,
      description: config.description,
      capabilities: config.capabilities as CapabilityId[],
      authMethods: config.authMethods,
      configSchema: {},
    },
    search: createSearchImplementation(impl),
    healthCheck: createHealthCheckImplementation(impl),
    configuration: {
      priority: config.priority,
      enabled: true,
      config: {
        baseUrl: config.baseUrl,
        boardToken: config.boardToken,
        companyId: config.companyId,
        listId: config.listId,
        site: config.site,
      },
    },
  }

  return createAndRegisterProvider(providerImpl)
}
