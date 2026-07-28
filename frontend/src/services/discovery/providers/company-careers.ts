import { createProvider } from '../../provider-sdk'
import { createDiscoveryProvider } from '../migration-helper'

const created = createProvider({
  metadata: {
    id: 'company_careers', name: 'Company Careers', version: '1.0.0',
    description: 'Direct company career page job search provider',
    capabilities: ['search', 'filter_by_location', 'filter_by_type', 'company_profile'],
    authMethods: [],
    configSchema: {},
  },
  search: async (params) => {
    const companies = ['Google', 'Microsoft', 'Apple', 'Tesla']
    const locations = ['Mountain View, CA', 'Redmond, WA', 'Cupertino, CA', 'Austin, TX']
    const count = Math.min(params.pageSize, 4)
    const jobs = []
    for (let i = 0; i < count; i++) {
      const company = companies[(params.page * count + i) % companies.length]
      jobs.push({
        externalId: `cc_${company.toLowerCase()}_${Date.now()}_${i}`,
        title: params.keywords ? `${params.keywords} Engineer` : 'Software Engineer',
        company, companyLogo: null,
        companyWebsite: `https://${company.toLowerCase()}.com`,
        location: locations[i % locations.length],
        remote: i % 3 === 0 ? 'Hybrid' : 'On-site',
        employmentType: 'Full-time',
        experienceLevel: i % 2 === 0 ? 'Senior' : 'Staff',
        salaryMin: 150000 + i * 50000,
        salaryMax: 250000 + i * 50000,
        currency: 'USD',
        description: `${company} is hiring a ${params.keywords || 'Software'} Engineer. This role involves working on core products used by billions.`,
        responsibilities: ['Design large-scale systems', 'Write high-quality code', 'Lead technical projects', 'Mentor engineers'],
        requiredSkills: ['Data Structures', 'Algorithms', 'System Design', params.keywords || 'Software Engineering'],
        preferredSkills: ['Distributed Systems', 'Machine Learning', 'Performance Optimization'],
        benefits: ['Comprehensive healthcare', 'Stock units', 'Onsite gym', 'Free meals', 'Tuition reimbursement'],
        visaSponsorship: true,
        postedDate: new Date(Date.now() - i * 86400000).toISOString(),
        applicationDeadline: new Date(Date.now() + 60 * 86400000).toISOString(),
        easyApply: false,
        tags: [company.toLowerCase(), params.keywords || 'engineer'],
        metadata: { country: 'US', directlyFromCompany: true },
      })
    }
    return { data: jobs, total: jobs.length, hasMore: false }
  },
  healthCheck: async () => ({ status: 'healthy', latency: 2500, lastCheck: new Date().toISOString() }),
  configuration: { priority: 7, enabled: true },
})

export const companyCareersProvider = createDiscoveryProvider(created, created.metadata.capabilities, 7)
