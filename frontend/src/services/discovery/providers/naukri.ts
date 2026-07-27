import type { JobProvider, SearchParams, SearchResult, RawJob, ProviderHealth } from '../types'

export const naukriProvider: JobProvider = {
  id: 'naukri',
  name: 'Naukri',
  enabled: true,
  priority: 3,
  capabilities: ['search', 'filter_by_location', 'filter_by_experience', 'filter_by_type'],

  async search(params: SearchParams): Promise<SearchResult> {
    const start = Date.now()
    try {
      const mockJobs: RawJob[] = generateMockJobs(params)
      return {
        jobs: mockJobs,
        totalResults: mockJobs.length,
        page: params.page,
        pageSize: params.pageSize,
        hasMore: params.page < 3,
        provider: 'naukri',
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
        provider: 'naukri',
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
      successRate: 0.9,
      averageLatency: 1800,
      errorCount: 5,
      availability: 0.94,
      consecutiveFailures: 0,
      lastError: null,
    }
  },
}

function generateMockJobs(params: SearchParams): RawJob[] {
  const count = Math.min(params.pageSize, 8)
  const jobs: RawJob[] = []
  const companies = ['TCS', 'Infosys', 'Wipro', 'HCL', 'Tech Mahindra', 'Cognizant', 'Capgemini', 'LTIMindtree']
  const locations = ['Bangalore', 'Mumbai', 'Hyderabad', 'Pune', 'Chennai', 'Delhi', 'Remote']

  for (let i = 0; i < count; i++) {
    const company = companies[(params.page * count + i) % companies.length]
    jobs.push({
      externalId: `nk_${Date.now()}_${i}`,
      title: params.keywords ? `${params.keywords} Developer` : 'Software Developer',
      company,
      companyLogo: null,
      companyWebsite: `https://${company.toLowerCase()}.com`,
      location: locations[i % locations.length],
      remote: i % 4 === 0 ? 'Remote' : 'On-site',
      employmentType: 'Full-time',
      experienceLevel: i % 2 === 0 ? '3-5 years' : '5-8 years',
      salaryMin: 600000 + i * 200000,
      salaryMax: 1200000 + i * 300000,
      currency: 'INR',
      description: `${company} is hiring ${params.keywords || 'Software'} Developers with experience in modern tech stacks. Join our team of innovators.`,
      responsibilities: ['Build scalable applications', 'Work in agile teams', 'Ensure code quality', 'Troubleshoot production issues'],
      requiredSkills: ['Java', 'Spring Boot', 'React', 'MySQL'],
      preferredSkills: ['Microservices', 'Docker', 'Kubernetes', 'AWS'],
      benefits: ['Health insurance', 'Provident fund', 'Annual bonus', 'Training programs'],
      visaSponsorship: null,
      postedDate: new Date(Date.now() - i * 86400000).toISOString(),
      applicationDeadline: new Date(Date.now() + 30 * 86400000).toISOString(),
      easyApply: false,
      tags: [params.keywords || 'software', 'india'],
      metadata: { country: 'IN', source: 'Naukri' },
    })
  }
  return jobs
}
