import { createATSProvider, type ATSProviderImplementation } from '../ats-provider-base'
import type { ATSJobRaw } from '../ats-types'
import { toJobProvider } from '../../discovery/migration-helper'

interface SuccessFactorsJob {
  id: string
  title: string
  location: string
  department: string
  description: string
  postedDate: string
  applyUrl: string
  externalId: string
  city: string
  state: string
  country: string
  employmentType: string
  experienceLevel: string
  jobFamily: string
}

interface SuccessFactorsResponse {
  total: number
  offset: number
  limit: number
  results: SuccessFactorsJob[]
}

function parseSuccessFactorsResponse(response: unknown, _providerId: string): ATSJobRaw[] {
  const data = response as SuccessFactorsResponse | SuccessFactorsJob[]
  const jobs = Array.isArray(data) ? data : (data as SuccessFactorsResponse).results ?? []
  return jobs.map((job: SuccessFactorsJob) => {
    const location = job.location || `${job.city ?? ''}${job.state ? ', ' + job.state : ''}${job.country ? ', ' + job.country : ''}`.replace(/^,\s/, '') || 'Remote'
    return {
      externalId: job.id || job.externalId,
      title: job.title,
      location,
      description: job.description || `Position at ${job.title}`,
      department: job.department || job.jobFamily,
      employmentType: job.employmentType || 'Full-time',
      postedDate: job.postedDate,
      applyUrl: job.applyUrl,
      metadata: { jobFamily: job.jobFamily, experienceLevel: job.experienceLevel },
    }
  })
}

const impl: ATSProviderImplementation = {
  config: {
    id: 'successfactors',
    name: 'SAP SuccessFactors',
    description: 'SAP SuccessFactors enterprise ATS job board provider',
    baseUrl: 'https://api.successfactors.com/recruiting/v1',
    endpoints: { jobs: '/jobs/{company_id}' },
    pagination: {
      style: 'offset_limit',
      offsetParam: 'offset',
      limitParam: 'limit',
      totalPath: ['total'],
      itemsPath: ['results'],
      defaultPageSize: 20,
      maxPageSize: 100,
    },
    rateLimitPerSecond: 5,
    timeoutMs: 15000,
    authMethods: [],
    capabilities: ['search', 'filter_by_location', 'filter_by_type'],
    priority: 20,
    version: '1.0.0',
    companyId: 'default',
  },
  parseResponse: parseSuccessFactorsResponse,
}

const created = createATSProvider(impl)
export const successfactorsProvider = toJobProvider(created)
