import { createProvider } from '../../provider-sdk'
import { createDiscoveryProvider } from '../migration-helper'
import { generateMockJobs } from '../mock-data'

const created = createProvider({
  metadata: {
    id: 'internshala', name: 'Internshala', version: '1.0.0',
    description: 'Internshala internship and job search provider for Indian students',
    capabilities: ['search', 'filter_by_location', 'filter_by_type'],
    authMethods: [],
    configSchema: {},
  },
  search: async (params) => {
    const mockJobs = generateMockJobs(params, 'internshala', ['Zomato', 'Swiggy', 'Flipkart', 'Myntra', 'Urban Company', 'Razorpay'], 6, 'Intern', 10000, 30000, {
      alwaysEasyApply: true, visaMod: 0,
      locationPool: ['Bangalore', 'Mumbai', 'Delhi', 'Hyderabad', 'Remote'],
      remoteMod: 3,
      expLevels: ['Internship'],
    })
    return { data: mockJobs, total: mockJobs.length, hasMore: params.page < 2 }
  },
  healthCheck: async () => ({ status: 'healthy', latency: 1100, lastCheck: new Date().toISOString() }),
  configuration: { priority: 8, enabled: true },
})

export const internshalaProvider = createDiscoveryProvider(created, created.metadata.capabilities, 8)
