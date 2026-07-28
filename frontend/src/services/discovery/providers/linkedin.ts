import { createProvider } from '../../provider-sdk'
import { createDiscoveryProvider } from '../migration-helper'
import { generateMockJobs } from '../mock-data'

const created = createProvider({
  metadata: {
    id: 'linkedin', name: 'LinkedIn', version: '1.0.0',
    description: 'LinkedIn job search provider',
    capabilities: ['search', 'filter_by_location', 'filter_by_experience', 'filter_by_type', 'easy_apply', 'company_profile', 'salary_range'],
    authMethods: [],
    configSchema: {},
  },
  search: async (params) => {
    const mockJobs = generateMockJobs(params, 'linkedin', ['Google', 'Microsoft', 'Amazon', 'Meta', 'Apple', 'Netflix', 'Stripe', 'Shopify'], 8, 'Engineer', 100000, 150000)
    return { data: mockJobs, total: mockJobs.length, hasMore: false }
  },
  healthCheck: async () => ({ status: 'healthy', latency: 1200, lastCheck: new Date().toISOString() }),
  configuration: { priority: 1, enabled: true },
})

export const linkedinProvider = createDiscoveryProvider(created, created.metadata.capabilities, 1)
