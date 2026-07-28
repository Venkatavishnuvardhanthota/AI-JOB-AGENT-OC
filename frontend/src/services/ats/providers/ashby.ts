import { createATSProvider, type ATSProviderImplementation } from '../ats-provider-base'
import type { ATSJobRaw } from '../ats-types'
import { toJobProvider } from '../../discovery/migration-helper'

interface AshbyPosting {
  id: string
  title: string
  team: { name: string }
  location: { name: string }
  employmentType: string
  descriptionHtml: string
  descriptionPlain: string
  salaryRange: { min: number | null; max: number | null; currency: string | null }
  updatedAt: string
  applyUrl: string
  requisitionId: string
}

interface AshbyResponse {
  jobPostings: AshbyPosting[]
  more: boolean
  cursor?: string
}

function parseAshbyResponse(response: unknown, providerId: string): ATSJobRaw[] {
  const data = response as AshbyResponse | AshbyPosting[]
  const postings = Array.isArray(data) ? data : (data as AshbyResponse).jobPostings ?? []
  return postings.map((posting: AshbyPosting) => ({
    externalId: posting.id,
    title: posting.title,
    location: posting.location?.name ?? 'Remote',
    description: posting.descriptionPlain || posting.descriptionHtml || '',
    department: posting.team?.name,
    employmentType: posting.employmentType,
    salaryMin: posting.salaryRange?.min ?? null,
    salaryMax: posting.salaryRange?.max ?? null,
    currency: posting.salaryRange?.currency ?? null,
    postedDate: posting.updatedAt,
    applyUrl: posting.applyUrl,
    metadata: { requisitionId: posting.requisitionId, teamId: posting.team?.name },
  }))
}

const impl: ATSProviderImplementation = {
  config: {
    id: 'ashby',
    name: 'Ashby',
    description: 'Ashby ATS job board provider',
    baseUrl: 'https://api.ashbyhq.com/posting-api',
    endpoints: { jobs: '/job-board/{list_id}' },
    pagination: {
      style: 'cursor',
      cursorParam: 'cursor',
      limitParam: 'limit',
      hasMorePath: ['more'],
      cursorPath: ['cursor'],
      itemsPath: ['jobPostings'],
      defaultPageSize: 25,
      maxPageSize: 100,
    },
    rateLimitPerSecond: 5,
    timeoutMs: 15000,
    authMethods: [],
    capabilities: ['search', 'filter_by_location', 'filter_by_type', 'salary_range'],
    priority: 13,
    version: '1.0.0',
    listId: 'default',
  },
  parseResponse: parseAshbyResponse,
}

const created = createATSProvider(impl)
export const ashbyProvider = toJobProvider(created)
