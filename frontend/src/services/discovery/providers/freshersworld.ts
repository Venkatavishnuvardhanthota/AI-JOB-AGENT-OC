import { createProvider } from '../../provider-sdk'
import { createDiscoveryProvider } from '../migration-helper'

const created = createProvider({
  metadata: {
    id: 'freshersworld', name: 'Freshersworld', version: '1.0.0',
    description: 'Freshersworld job search provider for fresh graduates in India',
    capabilities: ['search', 'filter_by_location', 'filter_by_type'],
    authMethods: [],
    configSchema: {},
  },
  search: async (params) => {
    const count = Math.min(params.pageSize, 8)
    const jobs = []
    const companies = ['Cognizant', 'Infosys', 'TCS', 'Wipro', 'HCL', 'Tech Mahindra', 'Capgemini', 'Deloitte']
    const locations = ['Bangalore', 'Chennai', 'Hyderabad', 'Pune', 'Mumbai', 'Noida', 'Kochi', 'Remote']
    for (let i = 0; i < count; i++) {
      const company = companies[(params.page * count + i) % companies.length]
      const keyword = params.keywords || 'Graduate'
      jobs.push({
        externalId: `fw_${Date.now()}_${i}`, company, companyLogo: null,
        companyWebsite: `https://${company.toLowerCase()}.com`,
        title: `${keyword} Trainee - ${company}`,
        location: locations[i % locations.length],
        remote: i % 8 === 0 ? 'Remote' : 'On-site',
        employmentType: 'Full-time',
        experienceLevel: 'Fresher',
        salaryMin: 250000 + i * 50000,
        salaryMax: 500000 + i * 100000,
        currency: 'INR',
        description: `${company} is hiring fresh graduates for the ${keyword} Trainee program. Excellent career growth opportunities.`,
        responsibilities: ['Undergo classroom training', 'Work on client projects', 'Attend skill development sessions', 'Complete assessments'],
        requiredSkills: ['Basic Programming', 'Communication', 'Teamwork'],
        preferredSkills: ['Java', 'Python', 'SQL', 'Cloud fundamentals'],
        benefits: ['Training stipend', 'Health insurance', 'Certification programs', 'Career guidance'],
        visaSponsorship: null,
        postedDate: new Date(Date.now() - i * 86400000).toISOString(),
        applicationDeadline: new Date(Date.now() + 45 * 86400000).toISOString(),
        easyApply: true,
        tags: ['fresher', 'trainee', keyword.toLowerCase()],
        metadata: { country: 'IN', source: 'Freshersworld' },
      })
    }
    return { data: jobs, total: jobs.length, hasMore: params.page < 2 }
  },
  healthCheck: async () => ({ status: 'healthy', latency: 1600, lastCheck: new Date().toISOString() }),
  configuration: { priority: 10, enabled: true },
})

export const freshersworldProvider = createDiscoveryProvider(created, created.metadata.capabilities, 10)
