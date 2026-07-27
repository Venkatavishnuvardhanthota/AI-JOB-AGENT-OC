import type { JobProvider, SearchParams, SearchResult, RawJob, ProviderHealth } from '../types'

export const indeedProvider: JobProvider = {
  id: 'indeed',
  name: 'Indeed',
  enabled: true,
  priority: 2,
  capabilities: ['search', 'filter_by_location', 'filter_by_salary', 'filter_by_type', 'easy_apply', 'salary_range'],

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
        provider: 'indeed',
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
        provider: 'indeed',
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
      successRate: 0.92,
      averageLatency: 1500,
      errorCount: 3,
      availability: 0.96,
      consecutiveFailures: 0,
      lastError: null,
    }
  },
}

function generateMockJobs(params: SearchParams): RawJob[] {
  const count = Math.min(params.pageSize, 10)
  const jobs: RawJob[] = []
  const companies = ['Deloitte', 'Accenture', 'IBM', 'Oracle', 'Salesforce', 'Adobe', 'Cisco', 'Intel', 'VMware', 'SAP']
  const locations = ['Chicago, IL', 'Boston, MA', 'Denver, CO', 'Atlanta, GA', 'Dallas, TX', 'Remote']

  for (let i = 0; i < count; i++) {
    const company = companies[(params.page * count + i) % companies.length]
    jobs.push({
      externalId: `in_${Date.now()}_${i}`,
      title: params.keywords ? `${params.keywords} Developer` : 'Full Stack Developer',
      company,
      companyLogo: null,
      companyWebsite: `https://${company.toLowerCase().replace(/\s+/g, '')}.com`,
      location: locations[i % locations.length],
      remote: i % 2 === 0 ? 'Remote' : 'On-site',
      employmentType: 'Full-time',
      experienceLevel: i % 3 === 0 ? 'Entry Level' : i % 3 === 1 ? 'Mid Level' : 'Senior',
      salaryMin: 80000 + i * 20000,
      salaryMax: 130000 + i * 25000,
      currency: 'USD',
      description: `${company} is looking for a talented ${params.keywords || 'Developer'} to join our growing team. You will work on cutting-edge projects.`,
      responsibilities: ['Develop and maintain web applications', 'Collaborate with cross-functional teams', 'Write unit and integration tests', 'Participate in agile ceremonies'],
      requiredSkills: ['JavaScript', 'React', 'Node.js', 'SQL'],
      preferredSkills: ['TypeScript', 'GraphQL', 'Docker', 'AWS'],
      benefits: ['Competitive salary', 'Health & dental', 'Stock options', 'Learning budget'],
      visaSponsorship: i % 4 !== 0,
      postedDate: new Date(Date.now() - i * 43200000).toISOString(),
      applicationDeadline: null,
      easyApply: true,
      tags: [params.keywords || 'developer', 'fullstack'],
      metadata: { country: 'US', source: 'Indeed' },
    })
  }
  return jobs
}
