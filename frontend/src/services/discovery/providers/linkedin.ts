import type { JobProvider, SearchParams, SearchResult, RawJob, ProviderHealth } from '../types'

export const linkedinProvider: JobProvider = {
  id: 'linkedin',
  name: 'LinkedIn',
  enabled: true,
  priority: 1,
  capabilities: ['search', 'filter_by_location', 'filter_by_experience', 'filter_by_type', 'easy_apply', 'company_profile', 'salary_range'],

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
        provider: 'linkedin',
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
        provider: 'linkedin',
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
      successRate: 0.95,
      averageLatency: 1200,
      errorCount: 2,
      availability: 0.98,
      consecutiveFailures: 0,
      lastError: null,
    }
  },
}

function generateMockJobs(params: SearchParams): RawJob[] {
  const count = Math.min(params.pageSize, 8)
  const jobs: RawJob[] = []
  const companies = ['Google', 'Microsoft', 'Amazon', 'Meta', 'Apple', 'Netflix', 'Stripe', 'Shopify']
  const locations = ['San Francisco, CA', 'New York, NY', 'Seattle, WA', 'Austin, TX', 'Remote']
  const skills = ['TypeScript', 'React', 'Node.js', 'Python', 'Go', 'AWS', 'Docker', 'Kubernetes']

  for (let i = 0; i < count; i++) {
    const company = companies[(params.page * count + i) % companies.length]
    jobs.push({
      externalId: `li_${Date.now()}_${i}`,
      title: params.keywords ? `${params.keywords} Engineer` : 'Software Engineer',
      company,
      companyLogo: null,
      companyWebsite: `https://${company.toLowerCase()}.com`,
      location: locations[i % locations.length],
      remote: i % 3 === 0 ? 'Remote' : i % 3 === 1 ? 'Hybrid' : 'On-site',
      employmentType: 'Full-time',
      experienceLevel: i % 2 === 0 ? 'Mid-Senior' : 'Associate',
      salaryMin: 100000 + i * 25000,
      salaryMax: 150000 + i * 30000,
      currency: 'USD',
      description: `Join ${company} as a ${params.keywords || 'Software'}. You will build and maintain scalable systems that serve millions of users.`,
      responsibilities: ['Design and implement new features', 'Write clean, maintainable code', 'Participate in code reviews', 'Mentor junior engineers'],
      requiredSkills: skills.slice(0, 4),
      preferredSkills: skills.slice(4, 7),
      benefits: ['Health insurance', '401(k) matching', 'Unlimited PTO', 'Remote work options'],
      visaSponsorship: i % 3 !== 0,
      postedDate: new Date(Date.now() - i * 86400000).toISOString(),
      applicationDeadline: null,
      easyApply: i % 2 === 0,
      tags: [params.keywords || 'software', 'engineering', company.toLowerCase()],
      metadata: { country: 'US', industry: 'Technology', companySize: '10000+' },
    })
  }
  return jobs
}
