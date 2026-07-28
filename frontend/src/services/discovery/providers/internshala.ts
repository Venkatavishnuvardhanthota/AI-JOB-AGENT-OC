import { createPortalProvider } from '../../portals'
import { createDiscoveryProvider } from '../migration-helper'

const config = {
  id: 'internshala' as const,
  name: 'Internshala',
  version: '1.0.0',
  description: 'Internshala internship and job search provider for Indian students',
  capabilities: ['search', 'filter_by_location', 'filter_by_type'],
  priority: 8,
  mockOptions: {
    companies: ['Zomato', 'Swiggy', 'Flipkart', 'Myntra', 'Urban Company', 'Razorpay'],
    count: 6,
    titleSuffix: 'Intern',
    salaryMin: 10000,
    salaryMax: 30000,
    locations: ['Bangalore', 'Mumbai', 'Delhi', 'Hyderabad', 'Remote'],
    alwaysEasyApply: true,
    remoteMod: 3,
    expLevels: ['Internship'],
  },
}

const created = createPortalProvider(config)
export const internshalaProvider = createDiscoveryProvider(created, config.capabilities, config.priority)
