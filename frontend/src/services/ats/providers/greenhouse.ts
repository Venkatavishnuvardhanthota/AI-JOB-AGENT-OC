import { createATSProvider, type ATSProviderImplementation } from '../ats-provider-base'
import type { ATSJobRaw } from '../ats-types'
import { toJobProvider } from '../../discovery/migration-helper'

interface GreenhouseJob {
  id: number
  title: string
  location: { name: string } | null
  offices: Array<{ name: string }>
  departments: Array<{ name: string }>
  metadata: unknown
  updated_at: string
  absolute_url: string
  internal_job_id: number
}

interface GreenhouseResponse {
  jobs: GreenhouseJob[]
  meta?: { total?: number; page?: number; per_page?: number }
}

function parseGreenhouseResponse(response: unknown, _providerId: string): ATSJobRaw[] {
  const data = response as GreenhouseResponse | GreenhouseJob[]
  const jobs = Array.isArray(data) ? data : (data as GreenhouseResponse).jobs ?? []
  return jobs.map((job: GreenhouseJob) => ({
    externalId: String(job.id),
    title: job.title,
    location: job.location?.name ?? 'Remote',
    description: `Position at ${job.title}`,
    department: job.departments?.[0]?.name,
    employmentType: 'Full-time',
    postedDate: job.updated_at,
    applyUrl: job.absolute_url,
    metadata: { offices: job.offices?.map(o => o.name), internalId: job.internal_job_id },
  }))
}

const impl: ATSProviderImplementation = {
  config: {
    id: 'greenhouse',
    name: 'Greenhouse',
    description: 'Greenhouse ATS job board provider',
    baseUrl: 'https://boards-api.greenhouse.io/v1/boards',
    endpoints: { jobs: '/{board_token}/jobs?content=true' },
    pagination: {
      style: 'page_per_page',
      pageParam: 'page',
      pageSizeParam: 'per_page',
      totalPath: ['meta', 'total'],
      itemsPath: ['jobs'],
      defaultPageSize: 20,
      maxPageSize: 100,
    },
    rateLimitPerSecond: 5,
    timeoutMs: 15000,
    authMethods: [],
    capabilities: ['search', 'filter_by_location', 'filter_by_type'],
    priority: 11,
    version: '1.0.0',
    boardToken: 'example',
  },
  parseResponse: parseGreenhouseResponse,
}

const created = createATSProvider(impl)
export const greenhouseProvider = toJobProvider(created)
