import type { JobProvider, SearchParams, SearchResult, RawJob, ProviderHealth } from '../types'

export const unstopProvider: JobProvider = {
  id: 'unstop',
  name: 'Unstop (Dare2Compete)',
  enabled: true,
  priority: 9,
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
        provider: 'unstop',
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
        provider: 'unstop',
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
      successRate: 0.91,
      averageLatency: 1300,
      errorCount: 3,
      availability: 0.93,
      consecutiveFailures: 0,
      lastError: null,
    }
  },
}

function generateMockJobs(params: SearchParams): RawJob[] {
  const count = Math.min(params.pageSize, 5)
  const jobs: RawJob[] = []
  const companies = ['Google', 'Microsoft', 'Amazon', 'Goldman Sachs', 'BCG']
  const locations = ['Bangalore', 'Mumbai', 'Gurgaon', 'Pune', 'Remote']

  for (let i = 0; i < count; i++) {
    const company = companies[(params.page * count + i) % companies.length]
    jobs.push({
      externalId: `un_${Date.now()}_${i}`,
      title: params.keywords ? `${params.keywords} - ${company}` : `${company} Campus Hiring`,
      company,
      companyLogo: null,
      companyWebsite: `https://${company.toLowerCase().replace(/\s+/g, '')}.com`,
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
  return jobs
}
