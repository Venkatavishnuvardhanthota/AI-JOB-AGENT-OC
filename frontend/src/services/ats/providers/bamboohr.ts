import { createATSProvider, type ATSProviderImplementation } from '../ats-provider-base'
import type { ATSJobRaw } from '../ats-types'
import { toJobProvider } from '../../discovery/migration-helper'

interface BambooHRJob {
  id: number
  title: string
  location: { city: string; state: string; country: string } | null
  department: string
  description: string
  status: string
  postedDate: string
  closingDate: string | null
  employmentType: string
  hiringLead: string
}

interface BambooHRResponse {
  total: number
  results: BambooHRJob[]
}

function parseBambooHRResponse(response: unknown, providerId: string): ATSJobRaw[] {
  const data = response as BambooHRResponse | BambooHRJob[]
  const jobs = Array.isArray(data) ? data : (data as BambooHRResponse).results ?? []
  return jobs.map((job: BambooHRJob) => {
    const loc = job.location
    const location = loc ? `${loc.city ?? ''}${loc.state ? ', ' + loc.state : ''}${loc.country ? ', ' + loc.country : ''}`.replace(/^,\s/, '') || 'Remote' : 'Remote'
    return {
      externalId: String(job.id),
      title: job.title,
      location,
      description: job.description || `Position at ${job.title}`,
      department: job.department,
      employmentType: job.employmentType || 'Full-time',
      postedDate: job.postedDate,
      metadata: { hiringLead: job.hiringLead, closingDate: job.closingDate, status: job.status },
    }
  })
}

const impl: ATSProviderImplementation = {
  config: {
    id: 'bamboohr',
    name: 'BambooHR',
    description: 'BambooHR enterprise ATS job board provider',
    baseUrl: 'https://api.bamboohr.com/api/gateway.php',
    endpoints: { jobs: '/{company_id}/v1/applicant_tracking/jobs' },
    pagination: {
      style: 'page_per_page',
      pageParam: 'page',
      pageSizeParam: 'limit',
      totalPath: ['total'],
      itemsPath: ['results'],
      defaultPageSize: 20,
      maxPageSize: 100,
    },
    rateLimitPerSecond: 5,
    timeoutMs: 15000,
    authMethods: [],
    capabilities: ['search', 'filter_by_location', 'filter_by_type'],
    priority: 17,
    version: '1.0.0',
    companyId: 'default',
  },
  parseResponse: parseBambooHRResponse,
}

const created = createATSProvider(impl)
export const bamboohrProvider = toJobProvider(created)
