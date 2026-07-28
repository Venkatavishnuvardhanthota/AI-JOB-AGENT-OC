import { createATSProvider, type ATSProviderImplementation } from '../ats-provider-base'
import type { ATSJobRaw } from '../ats-types'
import { toJobProvider } from '../../discovery/migration-helper'

interface OracleJob {
  id: string
  title: string
  location: string
  department: string
  description: string
  postedDate: string
  applyUrl: string
  requisitionId: string
  primaryLocation: string
  jobFamily: string
  jobFunction: string
  employmentType: string
  experienceLevel: string
  remote: string
}

interface OracleResponse {
  items: OracleJob[]
  totalResults: number
  hasMore: boolean
  offset: number
  limit: number
}

function parseOracleResponse(response: unknown, providerId: string): ATSJobRaw[] {
  const data = response as OracleResponse | OracleJob[]
  const jobs = Array.isArray(data) ? data : (data as OracleResponse).items ?? []
  return jobs.map((job: OracleJob) => ({
    externalId: job.id || job.requisitionId,
    title: job.title,
    location: job.primaryLocation || job.location || 'Remote',
    description: job.description || `Position at ${job.title}`,
    department: job.department || job.jobFamily,
    employmentType: job.employmentType || 'Full-time',
    postedDate: job.postedDate,
    applyUrl: job.applyUrl,
    metadata: { requisitionId: job.requisitionId, jobFunction: job.jobFunction, experienceLevel: job.experienceLevel, remote: job.remote },
  }))
}

const impl: ATSProviderImplementation = {
  config: {
    id: 'oracle',
    name: 'Oracle Recruiting',
    description: 'Oracle Recruiting enterprise ATS job board provider',
    baseUrl: 'https://{company_id}.oraclecloud.com/hcmRestApi/resources/latest',
    endpoints: { jobs: '/recruitingJobs' },
    pagination: {
      style: 'offset_limit',
      offsetParam: 'offset',
      limitParam: 'limit',
      totalPath: ['totalResults'],
      hasMorePath: ['hasMore'],
      itemsPath: ['items'],
      defaultPageSize: 20,
      maxPageSize: 100,
    },
    rateLimitPerSecond: 5,
    timeoutMs: 15000,
    authMethods: [],
    capabilities: ['search', 'filter_by_location', 'filter_by_type'],
    priority: 19,
    version: '1.0.0',
    companyId: 'default',
  },
  parseResponse: parseOracleResponse,
}

const created = createATSProvider(impl)
export const oracleProvider = toJobProvider(created)
