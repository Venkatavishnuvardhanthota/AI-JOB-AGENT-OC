import { createPortalProvider } from '../../portals'
import { createDiscoveryProvider } from '../migration-helper'

const config = {
  id: 'naukri' as const,
  name: 'Naukri',
  version: '1.0.0',
  description: 'Naukri.com job search provider for Indian market',
  capabilities: ['search', 'filter_by_location', 'filter_by_experience', 'filter_by_type'],
  priority: 3,
  mockOptions: {
    companies: ['TCS', 'Infosys', 'Wipro', 'HCL', 'Tech Mahindra', 'Cognizant', 'Capgemini', 'LTIMindtree'],
    count: 8,
    titleSuffix: 'Developer',
    salaryMin: 600000,
    salaryMax: 1200000,
    locations: ['Bangalore', 'Mumbai', 'Hyderabad', 'Pune', 'Chennai', 'Delhi', 'Remote'],
    alwaysEasyApply: false,
    remoteMod: 4,
    expLevels: ['3-5 years', '5-8 years'],
  },
}

const created = createPortalProvider(config)
export const naukriProvider = createDiscoveryProvider(created, config.capabilities, config.priority)
