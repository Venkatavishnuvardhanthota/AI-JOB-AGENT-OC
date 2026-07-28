import { createProvider } from '../../provider-sdk'
import { createDiscoveryProvider } from '../migration-helper'
import { generateMockJobs } from '../mock-data'

const created = createProvider({
  metadata: {
    id: 'foundit', name: 'Foundit (Monster)', version: '1.0.0',
    description: 'Foundit (formerly Monster) job search provider for Indian market',
    capabilities: ['search', 'filter_by_location', 'filter_by_type'],
    authMethods: [],
    configSchema: {},
  },
  search: async (params) => {
    const mockJobs = generateMockJobs(params, 'foundit', ['Genpact', 'Concentrix', 'WNS', 'EXL', 'Sutherland', 'Teleperformance'], 6, 'Process Associate', 300000, 600000, {
      alwaysEasyApply: true, visaMod: 0,
      locationPool: ['Gurgaon', 'Noida', 'Bangalore', 'Mumbai', 'Remote'],
      remoteMod: 5,
      expLevels: ['Entry Level'],
    })
    return { data: mockJobs, total: mockJobs.length, hasMore: false }
  },
  healthCheck: async () => ({ status: 'healthy', latency: 2000, lastCheck: new Date().toISOString() }),
  configuration: { priority: 4, enabled: true },
})

export const founditProvider = createDiscoveryProvider(created, created.metadata.capabilities, 4)
