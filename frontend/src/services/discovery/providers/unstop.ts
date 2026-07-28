import { createPortalProvider } from '../../portals'
import { createDiscoveryProvider } from '../migration-helper'

const config = {
  id: 'unstop' as const,
  name: 'Unstop (Dare2Compete)',
  version: '1.0.0',
  description: 'Unstop (formerly Dare2Compete) campus hiring and contest-based recruitment',
  capabilities: ['search', 'filter_by_location', 'filter_by_type'],
  priority: 9,
  mockOptions: {
    companies: ['Google', 'Microsoft', 'Amazon', 'Goldman Sachs', 'BCG'],
    count: 5,
    titleSuffix: 'Campus Hiring',
    salaryMin: 800000,
    salaryMax: 1500000,
    locations: ['Bangalore', 'Mumbai', 'Gurgaon', 'Pune', 'Remote'],
    alwaysEasyApply: true,
    remoteMod: 4,
    expLevels: ['Entry Level'],
  },
}

const created = createPortalProvider(config)
export const unstopProvider = createDiscoveryProvider(created, config.capabilities, config.priority)
