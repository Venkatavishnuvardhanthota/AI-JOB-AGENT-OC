import { createATSProvider, type ATSProviderImplementation } from '../ats-provider-base'
import type { ATSJobRaw } from '../ats-types'
import { toJobProvider } from '../../discovery/migration-helper'

interface ICIMSJob {
  id: string
  title: string
  location: string
  department: string
  description: string
  employmentType: string
  postedDate: string
  applyUrl: string
  externalId: string
  city: string
  state: string
  country: string
  categories: string[]
  experienceLevel: string
}

interface ICIMSResponse {
  totalCount: number
  pageNumber: number
  pageSize: number
  jobs: ICIMSJob[]
  hasMore: boolean
}

function parseICIMSResponse(response: unknown, providerId: string): ATSJobRaw[] {
  const data = response as ICIMSResponse | ICIMSJob[]
  const jobs = Array.isArray(data) ? data : (data as ICIMSResponse).jobs ?? []
  return jobs.map((job: ICIMSJob) => {
    const location = job.location || `${job.city ?? ''}${job.state ? ', ' + job.state : ''}${job.country ? ', ' + job.country : ''}`.replace(/^,\s/, '') || 'Remote'
    return {
      externalId: job.id || job.externalId,
      title: job.title,
      location,
      description: job.description || `Position at ${job.title}`,
      department: job.department,
      employmentType: job.employmentType,
      postedDate: job.postedDate,
      applyUrl: job.applyUrl,
      metadata: { categories: job.categories, experienceLevel: job.experienceLevel },
    }
  })
}

const impl: ATSProviderImplementation = {
  config: {
    id: 'icims',
    name: 'iCIMS',
    description: 'iCIMS enterprise ATS job board provider',
    baseUrl: 'https://api.icims.com',
    endpoints: { jobs: '/jobs/{company_id}/search' },
    pagination: {
      style: 'page_per_page',
      pageParam: 'page',
      pageSizeParam: 'pageSize',
      totalPath: ['totalCount'],
      hasMorePath: ['hasMore'],
      itemsPath: ['jobs'],
      defaultPageSize: 20,
      maxPageSize: 100,
    },
    rateLimitPerSecond: 5,
    timeoutMs: 15000,
    authMethods: [],
    capabilities: ['search', 'filter_by_location', 'filter_by_type'],
    priority: 18,
    version: '1.0.0',
    companyId: 'default',
  },
  parseResponse: parseICIMSResponse,
}

const created = createATSProvider(impl)
export const icimsProvider = toJobProvider(created)
