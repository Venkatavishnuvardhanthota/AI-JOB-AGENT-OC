import { createATSProvider, type ATSProviderImplementation } from '../ats-provider-base'
import type { ATSJobRaw } from '../ats-types'
import { toJobProvider } from '../../discovery/migration-helper'

interface LeverPosting {
  id: string
  text: string
  categories: {
    location: string
    department: string
    commitment: string
    team: string
  }
  description: string
  descriptionPlain: string
  lists: Array<{ text: string; content: string }>
  additional: string
  hostedUrl: string
  applyUrl: string
  createdAt: number
}

interface LeverResponse {
  total: number
  data: LeverPosting[]
}

function parseLeverResponse(response: unknown, _providerId: string): ATSJobRaw[] {
  const data = response as LeverResponse | LeverPosting[]
  const postings = Array.isArray(data) ? data : (data as LeverResponse).data ?? []
  return postings.map((posting: LeverPosting) => {
    const requirements = posting.lists?.filter(l => l.text.toLowerCase().includes('requirement') || l.text.toLowerCase().includes('qualification')).map(l => l.content) ?? []
    const responsibilities = posting.lists?.filter(l => l.text.toLowerCase().includes('responsibility') || l.text.toLowerCase().includes('about')).map(l => l.content) ?? []
    return {
      externalId: posting.id,
      title: posting.text,
      location: posting.categories?.location ?? 'Remote',
      description: posting.descriptionPlain || posting.description || '',
      department: posting.categories?.department,
      employmentType: posting.categories?.commitment,
      postedDate: posting.createdAt ? new Date(posting.createdAt * 1000).toISOString() : undefined,
      applyUrl: posting.applyUrl || posting.hostedUrl,
      requirements,
      responsibilities,
      metadata: { team: posting.categories?.team },
    }
  })
}

const impl: ATSProviderImplementation = {
  config: {
    id: 'lever',
    name: 'Lever',
    description: 'Lever ATS job board provider',
    baseUrl: 'https://api.lever.co/v0/postings',
    endpoints: { jobs: '/{site}?mode=json' },
    pagination: {
      style: 'offset_limit',
      offsetParam: 'offset',
      limitParam: 'limit',
      totalPath: ['total'],
      itemsPath: ['data'],
      defaultPageSize: 20,
      maxPageSize: 100,
    },
    rateLimitPerSecond: 5,
    timeoutMs: 15000,
    authMethods: [],
    capabilities: ['search', 'filter_by_location', 'filter_by_type'],
    priority: 12,
    version: '1.0.0',
    site: 'default',
  },
  parseResponse: parseLeverResponse,
}

const created = createATSProvider(impl)
export const leverProvider = toJobProvider(created)
