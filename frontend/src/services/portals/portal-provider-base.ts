import { createProvider, type ProviderImplementation } from '../provider-sdk'
import type { SearchParams, RawJob } from '../discovery/types'
import type { ProviderContext } from '../provider-sdk/types'
import type { PortalProviderConfig, PortalJobRaw } from './portal-types'
import { normalizePortalJob } from './portal-types'
import { toPortalSearchInput, generateMockJob } from './portal-filters'

function generateMockJobsData(params: SearchParams, config: PortalProviderConfig, providerId: string): { data: RawJob[]; total: number; hasMore: boolean } {
  const count = Math.min(params.pageSize, config.mockOptions.count)
  const jobs: RawJob[] = []

  for (let i = 0; i < count; i++) {
    const raw = generateMockJob(i, params.page, params, config.mockOptions, providerId)
    jobs.push(normalizePortalJob(raw as PortalJobRaw, providerId))
  }

  const total = jobs.length
  const hasMore = params.page < 3
  return { data: jobs, total, hasMore }
}

export function createPortalProvider(config: PortalProviderConfig): ReturnType<typeof createProvider> {
  const providerId = config.id

  const providerImpl: ProviderImplementation = {
    metadata: {
      id: providerId,
      name: config.name,
      version: config.version,
      description: config.description,
      capabilities: config.capabilities,
      authMethods: [],
      configSchema: {},
    },

    search: async (params: SearchParams, ctx: ProviderContext) => {
      const result = generateMockJobsData(params, config, providerId)
      return result
    },

    healthCheck: async () => ({
      status: 'healthy',
      latency: Math.floor(Math.random() * 1000) + 500,
      lastCheck: new Date().toISOString(),
    }),
  }

  return createProvider(providerImpl)
}
