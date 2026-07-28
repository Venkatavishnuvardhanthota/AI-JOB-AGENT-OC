import { createProvider } from '../../provider-sdk'
import { createDiscoveryProvider } from '../migration-helper'
import { generateMockJobs } from '../mock-data'

const created = createProvider({
  metadata: {
    id: 'wellfound', name: 'Wellfound (AngelList)', version: '1.0.0',
    description: 'Wellfound (AngelList) startup job search provider',
    capabilities: ['search', 'filter_by_location', 'filter_by_type', 'easy_apply', 'company_profile', 'salary_range'],
    authMethods: [],
    configSchema: {},
  },
  search: async (params) => {
    const mockJobs = generateMockJobs(params, 'wellfound', ['Rippling', 'Deel', 'Notion', 'Figma', 'Linear', 'Vercel'], 6, 'Engineer', 120000, 180000, {
      alwaysEasyApply: true, visaMod: 3,
      locationPool: ['San Francisco, CA', 'New York, NY', 'Remote', 'Remote'],
      remoteMod: 2,
      expLevels: ['Mid Level', 'Senior'],
    })
    return { data: mockJobs, total: mockJobs.length, hasMore: params.page < 2 }
  },
  healthCheck: async () => ({ status: 'healthy', latency: 900, lastCheck: new Date().toISOString() }),
  configuration: { priority: 5, enabled: true },
})

export const wellfoundProvider = createDiscoveryProvider(created, created.metadata.capabilities, 5)
