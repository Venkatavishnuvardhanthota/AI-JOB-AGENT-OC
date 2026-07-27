import type { JobProvider, SearchParams, SearchResult, RawJob, ProviderHealth } from '../types'

export const wellfoundProvider: JobProvider = {
  id: 'wellfound',
  name: 'Wellfound (AngelList)',
  enabled: true,
  priority: 5,
  capabilities: ['search', 'filter_by_location', 'filter_by_type', 'easy_apply', 'company_profile', 'salary_range'],

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
        provider: 'wellfound',
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
        provider: 'wellfound',
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
      successRate: 0.93,
      averageLatency: 900,
      errorCount: 1,
      availability: 0.97,
      consecutiveFailures: 0,
      lastError: null,
    }
  },
}

function generateMockJobs(params: SearchParams): RawJob[] {
  const count = Math.min(params.pageSize, 6)
  const jobs: RawJob[] = []
  const companies = ['Rippling', 'Deel', 'Notion', 'Figma', 'Linear', 'Vercel']
  const locations = ['San Francisco, CA', 'New York, NY', 'Remote', 'Remote']

  for (let i = 0; i < count; i++) {
    const company = companies[(params.page * count + i) % companies.length]
    jobs.push({
      externalId: `wf_${Date.now()}_${i}`,
      title: params.keywords ? `${params.keywords} Engineer` : 'Software Engineer',
      company,
      companyLogo: null,
      companyWebsite: `https://${company.toLowerCase()}.com`,
      location: locations[i % locations.length],
      remote: i % 2 === 0 ? 'Remote' : 'Hybrid',
      employmentType: 'Full-time',
      experienceLevel: i % 2 === 0 ? 'Mid Level' : 'Senior',
      salaryMin: 120000 + i * 30000,
      salaryMax: 180000 + i * 40000,
      currency: 'USD',
      description: `${company} is a well-funded startup looking for a ${params.keywords || 'Software'} Engineer to join our early team. Equity included.`,
      responsibilities: ['Build core product features', 'Work directly with founders', 'Shape engineering culture', 'Own end-to-end delivery'],
      requiredSkills: ['TypeScript', 'React', 'Node.js', 'PostgreSQL'],
      preferredSkills: ['GraphQL', 'tRPC', 'Prisma', 'Tailwind CSS'],
      benefits: ['Competitive equity', 'Health insurance', 'Flexible PTO', 'Home office stipend'],
      visaSponsorship: i % 3 === 0,
      postedDate: new Date(Date.now() - i * 3600000).toISOString(),
      applicationDeadline: null,
      easyApply: true,
      tags: [params.keywords || 'startup', 'engineer'],
      metadata: { country: 'US', fundingStage: 'Series A', teamSize: '10-50' },
    })
  }
  return jobs
}
