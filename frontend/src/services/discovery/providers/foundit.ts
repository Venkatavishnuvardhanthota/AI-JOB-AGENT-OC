import type { JobProvider, SearchParams, SearchResult, RawJob, ProviderHealth } from '../types'

export const founditProvider: JobProvider = {
  id: 'foundit',
  name: 'Foundit (Monster)',
  enabled: true,
  priority: 4,
  capabilities: ['search', 'filter_by_location', 'filter_by_type'],

  async search(params: SearchParams): Promise<SearchResult> {
    const start = Date.now()
    try {
      const mockJobs: RawJob[] = generateMockJobs(params)
      return {
        jobs: mockJobs,
        totalResults: mockJobs.length,
        page: params.page,
        pageSize: params.pageSize,
        hasMore: false,
        provider: 'foundit',
        duration: Date.now() - start,
        error: null,
      }
    } catch (err) {
      return {
        jobs: [],
        totalResults: 0,
        page: params.page,
        pageSize: params.pageSize,
        hasMore: false,
        provider: 'foundit',
        duration: Date.now() - start,
        error: err instanceof Error ? err.message : 'Unknown error',
      }
    }
  },

  async health(): Promise<ProviderHealth> {
    return {
      status: 'healthy',
      lastSuccess: new Date().toISOString(),
      lastFailure: null,
      successRate: 0.88,
      averageLatency: 2000,
      errorCount: 4,
      availability: 0.92,
      consecutiveFailures: 0,
      lastError: null,
    }
  },
}

function generateMockJobs(params: SearchParams): RawJob[] {
  const count = Math.min(params.pageSize, 6)
  const jobs: RawJob[] = []
  const companies = ['Genpact', 'Concentrix', 'WNS', 'EXL', 'Sutherland', 'Teleperformance']
  const locations = ['Gurgaon', 'Noida', 'Bangalore', 'Mumbai', 'Remote']

  for (let i = 0; i < count; i++) {
    const company = companies[(params.page * count + i) % companies.length]
    jobs.push({
      externalId: `ft_${Date.now()}_${i}`,
      title: params.keywords ? params.keywords : 'Process Associate',
      company,
      companyLogo: null,
      companyWebsite: `https://${company.toLowerCase()}.com`,
      location: locations[i % locations.length],
      remote: i % 5 === 0 ? 'Remote' : 'On-site',
      employmentType: i % 3 === 0 ? 'Contract' : 'Full-time',
      experienceLevel: 'Entry Level',
      salaryMin: 300000 + i * 100000,
      salaryMax: 600000 + i * 150000,
      currency: 'INR',
      description: `Exciting opportunity at ${company} for ${params.keywords || 'Process Associate'} role. Join our dynamic team.`,
      responsibilities: ['Handle client communications', 'Process documentation', 'Data entry and verification', 'Report generation'],
      requiredSkills: ['Communication', 'MS Office', 'Data Entry'],
      preferredSkills: ['Excel', 'CRM tools', 'Analytical skills'],
      benefits: ['Night shift allowance', 'Transport facility', 'Meal coupons', 'Insurance'],
      visaSponsorship: null,
      postedDate: new Date(Date.now() - i * 86400000).toISOString(),
      applicationDeadline: new Date(Date.now() + 15 * 86400000).toISOString(),
      easyApply: true,
      tags: [params.keywords || 'process'],
      metadata: { country: 'IN', source: 'Foundit' },
    })
  }
  return jobs
}
