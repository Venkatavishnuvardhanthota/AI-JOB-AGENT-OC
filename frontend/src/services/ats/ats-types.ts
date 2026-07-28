import type { RawJob } from '../discovery/types'
import type { AuthMethodType } from '../provider-sdk/types'

export type PaginationStyle = 'page_per_page' | 'offset_limit' | 'cursor'

export interface PaginationConfig {
  style: PaginationStyle
  pageParam?: string
  pageSizeParam?: string
  offsetParam?: string
  limitParam?: string
  cursorParam?: string
  totalPath?: string[]
  hasMorePath?: string[]
  cursorPath?: string[]
  itemsPath?: string[]
  defaultPageSize: number
  maxPageSize: number
}

export interface ATSEndpoints {
  jobs: string
  jobDetails?: string
}

export interface ATSProviderConfig {
  id: string
  name: string
  description: string
  baseUrl: string
  endpoints: ATSEndpoints
  pagination: PaginationConfig
  defaultParams?: Record<string, string>
  headers?: Record<string, string>
  rateLimitPerSecond?: number
  timeoutMs?: number
  authMethods: AuthMethodType[]
  capabilities: string[]
  priority: number
  version: string
  boardToken?: string
  companyId?: string
  listId?: string
  site?: string
}

export interface ATSJobRaw {
  externalId: string
  title: string
  location: string
  description: string
  descriptionHtml?: string
  department?: string
  employmentType?: string
  salaryMin?: number | null
  salaryMax?: number | null
  currency?: string | null
  postedDate?: string
  applyUrl?: string
  company?: string
  requirements?: string[]
  responsibilities?: string[]
  metadata?: Record<string, unknown>
}

export type ATSJobParser = (raw: unknown, providerId: string) => ATSJobRaw[]

export type ATSResponseParser = (response: unknown, providerId: string) => ATSJobRaw[]

export function normalizeATSJob(job: ATSJobRaw, providerId: string): RawJob {
  return {
    externalId: job.externalId,
    title: job.title,
    company: job.company ?? providerId,
    companyLogo: null,
    companyWebsite: null,
    location: job.location,
    remote: null,
    employmentType: job.employmentType ?? null,
    experienceLevel: null,
    salaryMin: job.salaryMin ?? null,
    salaryMax: job.salaryMax ?? null,
    currency: job.currency ?? null,
    description: job.description,
    responsibilities: job.responsibilities ?? [],
    requiredSkills: job.requirements ?? [],
    preferredSkills: [],
    benefits: [],
    visaSponsorship: null,
    postedDate: job.postedDate ?? null,
    applicationDeadline: null,
    easyApply: false,
    tags: [job.department ?? '', providerId].filter(Boolean),
    metadata: {
      ...job.metadata,
      department: job.department,
      atsProvider: providerId,
    },
  }
}
