import { createATSProvider, type ATSProviderImplementation } from '../ats-provider-base'
import type { ATSJobRaw } from '../ats-types'
import { toJobProvider } from '../../discovery/migration-helper'

interface WorkdayJob {
  id: string
  title: string
  location: { descriptor: string } | null
  businessUnit?: string
  businessSite?: string
  jobRequisitionId: string
  postedDate: string
  url: string
  jobFamily: string[]
  categories: string[]
  employmentType: string
}

interface WorkdayResponse {
  total: number
  results: WorkdayJob[]
  hasMore?: boolean
}

function parseWorkdayResponse(response: unknown, _providerId: string): ATSJobRaw[] {
  const data = response as WorkdayResponse | WorkdayJob[]
  const jobs = Array.isArray(data) ? data : (data as WorkdayResponse).results ?? []
  return jobs.map((job: WorkdayJob) => ({
    externalId: job.id || job.jobRequisitionId,
    title: job.title,
    location: job.location?.descriptor ?? 'Remote',
    description: `Position at ${job.title}`,
    department: job.businessUnit ?? job.jobFamily?.[0],
    employmentType: job.employmentType || 'Full-time',
    postedDate: job.postedDate,
    applyUrl: job.url,
    metadata: { requisitionId: job.jobRequisitionId, businessSite: job.businessSite, categories: job.categories, jobFamilies: job.jobFamily },
  }))
}

const impl: ATSProviderImplementation = {
  config: {
    id: 'workday',
    name: 'Workday',
    description: 'Workday enterprise ATS job board provider',
    baseUrl: 'https://{board_token}.myworkdayjobs.com/wday/cxs',
    endpoints: { jobs: '/{board_token}/jobs' },
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
    priority: 15,
    version: '1.0.0',
    boardToken: 'example',
  },
  parseResponse: parseWorkdayResponse,
}

const created = createATSProvider(impl)
export const workdayProvider = toJobProvider(created)
