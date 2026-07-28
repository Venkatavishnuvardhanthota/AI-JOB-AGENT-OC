import { createPortalProvider } from '../../portals'
import { createDiscoveryProvider } from '../migration-helper'

const config = {
  id: 'foundit' as const,
  name: 'Foundit (Monster)',
  version: '1.0.0',
  description: 'Foundit (formerly Monster) job search provider for Indian market',
  capabilities: ['search', 'filter_by_location', 'filter_by_type'],
  priority: 4,
  mockOptions: {
    companies: ['Genpact', 'Concentrix', 'WNS', 'EXL', 'Sutherland', 'Teleperformance'],
    count: 6,
    titleSuffix: 'Process Associate',
    salaryMin: 300000,
    salaryMax: 600000,
    locations: ['Gurgaon', 'Noida', 'Bangalore', 'Mumbai', 'Remote'],
    alwaysEasyApply: true,
    remoteMod: 5,
    expLevels: ['Entry Level'],
  },
}

const created = createPortalProvider(config)
export const founditProvider = createDiscoveryProvider(created, config.capabilities, config.priority)
