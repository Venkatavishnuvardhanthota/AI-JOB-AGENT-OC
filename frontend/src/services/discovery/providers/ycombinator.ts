import { createProvider } from '../../provider-sdk'
import { createDiscoveryProvider } from '../migration-helper'
import { generateMockJobs } from '../mock-data'

const created = createProvider({
  metadata: {
    id: 'ycombinator', name: 'Y Combinator Jobs', version: '1.0.0',
    description: 'Y Combinator backed startup job search provider',
    capabilities: ['search', 'filter_by_type', 'easy_apply', 'company_profile'],
    authMethods: [],
    configSchema: {},
  },
  search: async (params) => {
    const mockJobs = generateMockJobs(params, 'ycombinator', ['Brex', 'Ramp', 'Zepto', 'Razorpay', 'Groww'], 5, 'Engineer - Early Employee', 100000, 160000, {
      alwaysEasyApply: true, visaMod: 0, remoteMod: 1,
      locationPool: ['Remote', 'San Francisco, CA', 'Bangalore', 'Remote'],
      expLevels: ['Mid-Senior'],
    })
    return { data: mockJobs, total: mockJobs.length, hasMore: false }
  },
  healthCheck: async () => ({ status: 'healthy', latency: 700, lastCheck: new Date().toISOString() }),
  configuration: { priority: 6, enabled: true },
})

export const ycombinatorProvider = createDiscoveryProvider(created, created.metadata.capabilities, 6)
