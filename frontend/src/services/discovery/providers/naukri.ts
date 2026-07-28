import { createProvider } from '../../provider-sdk'
import { createDiscoveryProvider } from '../migration-helper'
import { generateMockJobs } from '../mock-data'

const created = createProvider({
  metadata: {
    id: 'naukri', name: 'Naukri', version: '1.0.0',
    description: 'Naukri.com job search provider for Indian market',
    capabilities: ['search', 'filter_by_location', 'filter_by_experience', 'filter_by_type'],
    authMethods: [],
    configSchema: {},
  },
  search: async (params) => {
    const mockJobs = generateMockJobs(params, 'naukri', ['TCS', 'Infosys', 'Wipro', 'HCL', 'Tech Mahindra', 'Cognizant', 'Capgemini', 'LTIMindtree'], 8, 'Developer', 600000, 1200000, {
      alwaysEasyApply: false, visaMod: 0,
      locationPool: ['Bangalore', 'Mumbai', 'Hyderabad', 'Pune', 'Chennai', 'Delhi', 'Remote'],
      remoteMod: 4,
      expLevels: ['3-5 years', '5-8 years'],
    })
    return { data: mockJobs, total: mockJobs.length, hasMore: params.page < 3 }
  },
  healthCheck: async () => ({ status: 'healthy', latency: 1800, lastCheck: new Date().toISOString() }),
  configuration: { priority: 3, enabled: true },
})

export const naukriProvider = createDiscoveryProvider(created, created.metadata.capabilities, 3)
