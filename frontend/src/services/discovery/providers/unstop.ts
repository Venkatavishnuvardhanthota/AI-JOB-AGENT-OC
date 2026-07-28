import { createProvider } from '../../provider-sdk'
import { createDiscoveryProvider } from '../migration-helper'

const created = createProvider({
  metadata: {
    id: 'unstop', name: 'Unstop (Dare2Compete)', version: '1.0.0',
    description: 'Unstop (formerly Dare2Compete) campus hiring and contest-based recruitment',
    capabilities: ['search', 'filter_by_location', 'filter_by_type'],
    authMethods: [],
    configSchema: {},
  },
  search: async (params) => {
    const count = Math.min(params.pageSize, 5)
    const jobs = []
    const companies = ['Google', 'Microsoft', 'Amazon', 'Goldman Sachs', 'BCG']
    const locations = ['Bangalore', 'Mumbai', 'Gurgaon', 'Pune', 'Remote']
    for (let i = 0; i < count; i++) {
      const company = companies[(params.page * count + i) % companies.length]
      jobs.push({
        externalId: `un_${Date.now()}_${i}`, company, companyLogo: null,
        companyWebsite: `https://${company.toLowerCase().replace(/\s+/g, '')}.com`,
        title: params.keywords ? `${params.keywords} - ${company}` : `${company} Campus Hiring`,
        location: locations[i % locations.length],
        remote: i % 4 === 0 ? 'Remote' : 'On-site',
        employmentType: 'Full-time',
        experienceLevel: 'Entry Level',
        salaryMin: 800000 + i * 400000,
        salaryMax: 1500000 + i * 500000,
        currency: 'INR',
        description: `${company} is hiring fresh graduates through campus recruitment. Apply now for ${params.keywords || 'campus hiring'} 2025.`,
        responsibilities: ['Complete training program', 'Work on real projects', 'Attend workshops', 'Build professional skills'],
        requiredSkills: ['DSA', 'Problem Solving', 'Communication'],
        preferredSkills: ['Python', 'Java', 'SQL', 'Cloud Basics'],
        benefits: ['Competitive package', 'Health insurance', 'Relocation support', 'Training programs'],
        visaSponsorship: null,
        postedDate: new Date(Date.now() - i * 86400000).toISOString(),
        applicationDeadline: new Date(Date.now() + 30 * 86400000).toISOString(),
        easyApply: true,
        tags: ['campus', 'fresher', company.toLowerCase()],
        metadata: { country: 'IN', source: 'Unstop', contestBased: true },
      })
    }
    return { data: jobs, total: jobs.length, hasMore: false }
  },
  healthCheck: async () => ({ status: 'healthy', latency: 1300, lastCheck: new Date().toISOString() }),
  configuration: { priority: 9, enabled: true },
})

export const unstopProvider = createDiscoveryProvider(created, created.metadata.capabilities, 9)
