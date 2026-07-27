import type { JobProvider, SearchParams, SearchResult, RawJob, ProviderHealth } from '../types'

export const ycombinatorProvider: JobProvider = {
  id: 'ycombinator',
  name: 'Y Combinator Jobs',
  enabled: true,
  priority: 6,
  capabilities: ['search', 'filter_by_type', 'easy_apply', 'company_profile'],

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
        provider: 'ycombinator',
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
        provider: 'ycombinator',
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
      successRate: 0.96,
      averageLatency: 700,
      errorCount: 0,
      availability: 0.99,
      consecutiveFailures: 0,
      lastError: null,
    }
  },
}

function generateMockJobs(params: SearchParams): RawJob[] {
  const count = Math.min(params.pageSize, 5)
  const jobs: RawJob[] = []
  const companies = ['Brex', 'Ramp', 'Zepto', 'Razorpay', 'Groww']
  const locations = ['Remote', 'San Francisco, CA', 'Bangalore', 'Remote']

  for (let i = 0; i < count; i++) {
    const company = companies[(params.page * count + i) % companies.length]
    jobs.push({
      externalId: `yc_${Date.now()}_${i}`,
      title: params.keywords ? `${params.keywords} Engineer - Early Employee` : 'Founding Engineer',
      company,
      companyLogo: null,
      companyWebsite: `https://${company.toLowerCase()}.com`,
      location: locations[i % locations.length],
      remote: 'Remote',
      employmentType: 'Full-time',
      experienceLevel: 'Mid-Senior',
      salaryMin: 100000 + i * 25000,
      salaryMax: 160000 + i * 35000,
      currency: 'USD',
      description: `Join YC-backed ${company} as an early engineer. Work on high-impact problems with a world-class team. Significant equity package.`,
      responsibilities: ['Build and ship product features', 'Contribute to technical architecture', 'Hire and mentor team members', 'Drive technical roadmap'],
      requiredSkills: ['JavaScript', 'React', 'Python', 'SQL'],
      preferredSkills: ['TypeScript', 'AWS', 'Docker', 'System Design'],
      benefits: ['Significant equity', 'Competitive salary', 'Health benefits', 'Flexible work'],
      visaSponsorship: null,
      postedDate: new Date(Date.now() - i * 86400000).toISOString(),
      applicationDeadline: null,
      easyApply: true,
      tags: ['startup', 'yc-backed', params.keywords || 'engineer'],
      metadata: { country: 'US', ycBatch: 'W22', source: 'Y Combinator' },
    })
  }
  return jobs
}
