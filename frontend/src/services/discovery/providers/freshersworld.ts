import type { JobProvider, SearchParams, SearchResult, RawJob, ProviderHealth } from '../types'

export const freshersworldProvider: JobProvider = {
  id: 'freshersworld',
  name: 'Freshersworld',
  enabled: true,
  priority: 10,
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
        provider: 'freshersworld',
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
        provider: 'freshersworld',
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
      successRate: 0.89,
      averageLatency: 1600,
      errorCount: 6,
      availability: 0.91,
      consecutiveFailures: 0,
      lastError: null,
    }
  },
}

function generateMockJobs(params: SearchParams): RawJob[] {
  const count = Math.min(params.pageSize, 8)
  const jobs: RawJob[] = []
  const companies = ['Cognizant', 'Infosys', 'TCS', 'Wipro', 'HCL', 'Tech Mahindra', 'Capgemini', 'Deloitte']
  const locations = ['Bangalore', 'Chennai', 'Hyderabad', 'Pune', 'Mumbai', 'Noida', 'Kochi', 'Remote']

  for (let i = 0; i < count; i++) {
    const company = companies[(params.page * count + i) % companies.length]
    jobs.push({
      externalId: `fw_${Date.now()}_${i}`,
      title: `${params.keywords || 'Graduate'} Trainee - ${company}`,
      company,
      companyLogo: null,
      companyWebsite: `https://${company.toLowerCase()}.com`,
      location: locations[i % locations.length],
      remote: i % 8 === 0 ? 'Remote' : 'On-site',
      employmentType: 'Full-time',
      experienceLevel: 'Fresher',
      salaryMin: 250000 + i * 50000,
      salaryMax: 500000 + i * 100000,
      currency: 'INR',
      description: `${company} is hiring fresh graduates for the ${params.keywords || 'Graduate'} Trainee program. Excellent career growth opportunities.`,
      responsibilities: ['Undergo classroom training', 'Work on client projects', 'Attend skill development sessions', 'Complete assessments'],
      requiredSkills: ['Basic Programming', 'Communication', 'Teamwork'],
      preferredSkills: ['Java', 'Python', 'SQL', 'Cloud fundamentals'],
      benefits: ['Training stipend', 'Health insurance', 'Certification programs', 'Career guidance'],
      visaSponsorship: null,
      postedDate: new Date(Date.now() - i * 86400000).toISOString(),
      applicationDeadline: new Date(Date.now() + 45 * 86400000).toISOString(),
      easyApply: true,
      tags: ['fresher', 'trainee', params.keywords || 'graduate'],
      metadata: { country: 'IN', source: 'Freshersworld' },
    })
  }
  return jobs
}
