import type { JobProvider, SearchParams, SearchResult, RawJob, ProviderHealth } from '../types'

export const companyCareersProvider: JobProvider = {
  id: 'company_careers',
  name: 'Company Careers',
  enabled: true,
  priority: 7,
  capabilities: ['search', 'filter_by_location', 'filter_by_type', 'company_profile'],

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
        provider: 'company_careers',
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
        provider: 'company_careers',
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
      successRate: 0.97,
      averageLatency: 2500,
      errorCount: 1,
      availability: 0.95,
      consecutiveFailures: 0,
      lastError: null,
    }
  },
}

function generateMockJobs(params: SearchParams): RawJob[] {
  const count = Math.min(params.pageSize, 4)
  const jobs: RawJob[] = []
  const companies = ['Google', 'Microsoft', 'Apple', 'Tesla']
  const urls = ['careers.google.com', 'careers.microsoft.com', 'jobs.apple.com', 'tesla.com/careers']
  const locations = ['Mountain View, CA', 'Redmond, WA', 'Cupertino, CA', 'Austin, TX']

  for (let i = 0; i < count; i++) {
    const company = companies[(params.page * count + i) % companies.length]
    jobs.push({
      externalId: `cc_${company.toLowerCase()}_${Date.now()}_${i}`,
      title: params.keywords ? `${params.keywords} Engineer` : 'Software Engineer',
      company,
      companyLogo: null,
      companyWebsite: `https://${company.toLowerCase()}.com`,
      location: locations[i % locations.length],
      remote: i % 3 === 0 ? 'Hybrid' : 'On-site',
      employmentType: 'Full-time',
      experienceLevel: i % 2 === 0 ? 'Senior' : 'Staff',
      salaryMin: 150000 + i * 50000,
      salaryMax: 250000 + i * 50000,
      currency: 'USD',
      description: `${company} is hiring a ${params.keywords || 'Software'} Engineer. This role involves working on core products used by billions.`,
      responsibilities: ['Design large-scale systems', 'Write high-quality code', 'Lead technical projects', 'Mentor engineers'],
      requiredSkills: ['Data Structures', 'Algorithms', 'System Design', params.keywords || 'Software Engineering'],
      preferredSkills: ['Distributed Systems', 'Machine Learning', 'Performance Optimization'],
      benefits: ['Comprehensive healthcare', 'Stock units', 'Onsite gym', 'Free meals', 'Tuition reimbursement'],
      visaSponsorship: true,
      postedDate: new Date(Date.now() - i * 86400000).toISOString(),
      applicationDeadline: new Date(Date.now() + 60 * 86400000).toISOString(),
      easyApply: false,
      tags: [company.toLowerCase(), params.keywords || 'engineer'],
      metadata: { country: 'US', source: urls[i % urls.length], directlyFromCompany: true },
    })
  }
  return jobs
}
