import { createPortalProvider } from '../../portals'
import { createDiscoveryProvider } from '../migration-helper'

const config = {
  id: 'freshersworld' as const,
  name: 'Freshersworld',
  version: '1.0.0',
  description: 'Freshersworld job search provider for fresh graduates in India',
  capabilities: ['search', 'filter_by_location', 'filter_by_type'],
  priority: 10,
  mockOptions: {
    companies: ['Cognizant', 'Infosys', 'TCS', 'Wipro', 'HCL', 'Tech Mahindra', 'Capgemini', 'Deloitte'],
    count: 8,
    titleSuffix: 'Trainee',
    salaryMin: 250000,
    salaryMax: 500000,
    locations: ['Bangalore', 'Chennai', 'Hyderabad', 'Pune', 'Mumbai', 'Noida', 'Kochi', 'Remote'],
    alwaysEasyApply: true,
    remoteMod: 8,
    expLevels: ['Fresher'],
  },
}

const created = createPortalProvider(config)
export const freshersworldProvider = createDiscoveryProvider(created, config.capabilities, config.priority)
