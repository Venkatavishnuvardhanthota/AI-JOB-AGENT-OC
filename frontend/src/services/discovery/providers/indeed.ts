import { createProvider } from '../../provider-sdk'
import { createDiscoveryProvider } from '../migration-helper'
import { generateMockJobs } from '../mock-data'

const created = createProvider({
  metadata: {
    id: 'indeed', name: 'Indeed', version: '1.0.0',
    description: 'Indeed job search provider',
    capabilities: ['search', 'filter_by_location', 'filter_by_salary', 'filter_by_type', 'easy_apply', 'salary_range'],
    authMethods: [],
    configSchema: {},
  },
  search: async (params) => {
    const mockJobs = generateMockJobs(params, 'indeed', ['Deloitte', 'Accenture', 'IBM', 'Oracle', 'Salesforce', 'Adobe', 'Cisco', 'Intel', 'VMware', 'SAP'], 10, 'Developer', 80000, 130000, {
      alwaysEasyApply: true, visaMod: 4,
      locationPool: ['Chicago, IL', 'Boston, MA', 'Denver, CO', 'Atlanta, GA', 'Dallas, TX', 'Remote'],
      remoteMod: 2,
      expLevels: ['Entry Level', 'Mid Level', 'Senior'],
    })
    return { data: mockJobs, total: mockJobs.length, hasMore: params.page < 2 }
  },
  healthCheck: async () => ({ status: 'healthy', latency: 1500, lastCheck: new Date().toISOString() }),
  configuration: { priority: 2, enabled: true },
})

export const indeedProvider = createDiscoveryProvider(created, created.metadata.capabilities, 2)
