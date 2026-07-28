import { createATSProvider, type ATSProviderImplementation } from '../ats-provider-base'
import type { ATSJobRaw } from '../ats-types'
import { toJobProvider } from '../../discovery/migration-helper'

interface SRPosting {
  id: string
  name: string
  department: { label: string }
  location: { city: string; country: string }
  type: { label: string }
  publishedAt: string
  applyUrl: string
  ref: string
}

interface SRResponse {
  totalFound: number
  content: SRPosting[]
}

function parseSmartRecruitersResponse(response: unknown, _providerId: string): ATSJobRaw[] {
  const data = response as SRResponse | SRPosting[]
  const postings = Array.isArray(data) ? data : (data as SRResponse).content ?? []
  return postings.map((posting: SRPosting) => ({
    externalId: posting.id,
    title: posting.name,
    location: posting.location ? `${posting.location.city ?? ''}, ${posting.location.country ?? ''}`.replace(/^,\s/, '') : 'Remote',
    description: `Position at ${posting.name}`,
    department: posting.department?.label,
    employmentType: posting.type?.label,
    postedDate: posting.publishedAt,
    applyUrl: posting.applyUrl,
    metadata: { reqId: posting.ref },
  }))
}

const impl: ATSProviderImplementation = {
  config: {
    id: 'smartrecruiters',
    name: 'SmartRecruiters',
    description: 'SmartRecruiters ATS job board provider',
    baseUrl: 'https://api.smartrecruiters.com/v1/companies',
    endpoints: { jobs: '/{company_id}/postings' },
    pagination: {
      style: 'page_per_page',
      pageParam: 'page',
      pageSizeParam: 'limit',
      totalPath: ['totalFound'],
      itemsPath: ['content'],
      defaultPageSize: 20,
      maxPageSize: 100,
    },
    rateLimitPerSecond: 5,
    timeoutMs: 15000,
    authMethods: [],
    capabilities: ['search', 'filter_by_location', 'filter_by_type'],
    priority: 14,
    version: '1.0.0',
    companyId: 'default',
  },
  parseResponse: parseSmartRecruitersResponse,
}

const created = createATSProvider(impl)
export const smartrecruitersProvider = toJobProvider(created)
