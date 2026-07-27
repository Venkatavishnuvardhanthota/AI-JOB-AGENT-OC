import type { JobProvider, SearchParams, SearchResult, RawJob, ProviderHealth } from '../types'

export const internshalaProvider: JobProvider = {
  id: 'internshala',
  name: 'Internshala',
  enabled: true,
  priority: 8,
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
        hasMore: params.page < 2,
        provider: 'internshala',
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
        provider: 'internshala',
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
      successRate: 0.94,
      averageLatency: 1100,
      errorCount: 2,
      availability: 0.96,
      consecutiveFailures: 0,
      lastError: null,
    }
  },
}

function generateMockJobs(params: SearchParams): RawJob[] {
  const count = Math.min(params.pageSize, 6)
  const jobs: RawJob[] = []
  const companies = ['Zomato', 'Swiggy', 'Flipkart', 'Myntra', 'Urban Company', 'Razorpay']
  const locations = ['Bangalore', 'Mumbai', 'Delhi', 'Hyderabad', 'Remote']

  for (let i = 0; i < count; i++) {
    const company = companies[(params.page * count + i) % companies.length]
    jobs.push({
      externalId: `is_${Date.now()}_${i}`,
      title: params.keywords ? `${params.keywords} Intern` : 'Software Development Intern',
      company,
      companyLogo: null,
      companyWebsite: `https://${company.toLowerCase()}.com`,
      location: locations[i % locations.length],
      remote: i % 3 === 0 ? 'Remote' : 'On-site',
      employmentType: 'Internship',
      experienceLevel: 'Internship',
      salaryMin: 10000 + i * 5000,
      salaryMax: 30000 + i * 10000,
      currency: 'INR',
      description: `Join ${company} as a ${params.keywords || 'Software Development'} Intern. Great learning opportunity with a fast-growing company.`,
      responsibilities: ['Assist in development tasks', 'Learn from senior engineers', 'Contribute to real projects', 'Attend team standups'],
      requiredSkills: ['HTML', 'CSS', 'JavaScript', 'Basic Programming'],
      preferredSkills: ['React', 'Node.js', 'Python', 'SQL'],
      benefits: ['Certificate', 'Letter of recommendation', 'Stipend', 'Flexible hours'],
      visaSponsorship: null,
      postedDate: new Date(Date.now() - i * 86400000).toISOString(),
      applicationDeadline: new Date(Date.now() + 14 * 86400000).toISOString(),
      easyApply: true,
      tags: ['internship', params.keywords || 'development'],
      metadata: { country: 'IN', source: 'Internshala' },
    })
  }
  return jobs
}
