import { createATSProvider, type ATSProviderImplementation } from '../ats-provider-base'
import type { ATSJobRaw } from '../ats-types'
import { toJobProvider } from '../../discovery/migration-helper'

interface JobviteJob {
  id: string
  title: string
  location: string
  department: string
  description: string
  employmentType: string
  postedDate: string
  applyUrl: string
  requisitionId: string
  category: string
  questions: Array<{ label: string; required: boolean }>
}

interface JobviteResponse {
  total: number
  page: number
  pageSize: number
  jobs: JobviteJob[]
}

function parseJobviteResponse(response: unknown, _providerId: string): ATSJobRaw[] {
  const data = response as JobviteResponse | JobviteJob[]
  const jobs = Array.isArray(data) ? data : (data as JobviteResponse).jobs ?? []
  return jobs.map((job: JobviteJob) => ({
    externalId: job.id || job.requisitionId,
    title: job.title,
    location: job.location || 'Remote',
    description: job.description || `Position at ${job.title}`,
    department: job.department || job.category,
    employmentType: job.employmentType,
    postedDate: job.postedDate,
    applyUrl: job.applyUrl,
    metadata: { requisitionId: job.requisitionId, category: job.category, hasQuestions: (job.questions ?? []).length > 0 },
  }))
}

const impl: ATSProviderImplementation = {
  config: {
    id: 'jobvite',
    name: 'Jobvite',
    description: 'Jobvite enterprise ATS job board provider',
    baseUrl: 'https://jobs.jobvite.com',
    endpoints: { jobs: '/{site}/api/v2/jobs' },
    pagination: {
      style: 'page_per_page',
      pageParam: 'page',
      pageSizeParam: 'pageSize',
      totalPath: ['total'],
      itemsPath: ['jobs'],
      defaultPageSize: 20,
      maxPageSize: 100,
    },
    defaultParams: { format: 'json' },
    rateLimitPerSecond: 5,
    timeoutMs: 15000,
    authMethods: [],
    capabilities: ['search', 'filter_by_location', 'filter_by_type'],
    priority: 16,
    version: '1.0.0',
    site: 'default',
  },
  parseResponse: parseJobviteResponse,
}

const created = createATSProvider(impl)
export const jobviteProvider = toJobProvider(created)
