import type { SearchParams } from '../discovery/types'
import type { PortalMockOptions } from './portal-types'

export interface PortalSearchInput {
  keywords: string
  location?: string
  page: number
  pageSize: number
  employmentType?: string
  remote?: string
  experienceLevel?: string
  salaryMin?: number
  salaryMax?: number
}

export function toPortalSearchInput(params: SearchParams): PortalSearchInput {
  return {
    keywords: params.keywords,
    location: params.location ?? undefined,
    page: params.page,
    pageSize: params.pageSize,
    employmentType: params.employmentType ?? undefined,
    remote: params.remote ?? undefined,
    experienceLevel: params.experienceLevel ?? undefined,
    salaryMin: params.salaryMin ?? undefined,
    salaryMax: params.salaryMax ?? undefined,
  }
}

export function buildSearchQuery(input: PortalSearchInput, extraParams?: Record<string, string>): string {
  const query: Record<string, string> = {
    q: input.keywords,
    page: String(input.page),
    pageSize: String(input.pageSize),
    ...extraParams,
  }
  if (input.location) query.location = input.location
  if (input.employmentType) query.employment_type = input.employmentType
  if (input.remote) query.remote = input.remote
  if (input.experienceLevel) query.experience_level = input.experienceLevel
  return new URLSearchParams(query).toString()
}

function getCompany(count: number, page: number, i: number, companies: string[]): string {
  return companies[(page * count + i) % companies.length]
}

function getLocation(i: number, locations: string[]): string {
  return locations[i % locations.length]
}

export function generateMockJob(
  i: number,
  page: number,
  params: SearchParams,
  opts: PortalMockOptions,
  providerId: string
) {
  const count = Math.min(params.pageSize, opts.count)
  const company = getCompany(count, page, i, opts.companies)
  const locations = opts.locations ?? ['Bangalore', 'Mumbai', 'Hyderabad', 'Pune', 'Chennai', 'Delhi', 'Remote']
  const remoteVal = opts.remoteMod !== undefined ? (i % opts.remoteMod === 0 ? 'Remote' : 'On-site') : 'On-site'
  const expLevel = opts.expLevels ? opts.expLevels[i % opts.expLevels.length] : 'Entry Level'
  const keyword = params.keywords || 'Professional'
  const now = Date.now()

  return {
    externalId: `${providerId}_${now}_${i}`,
    title: `${keyword} ${opts.titleSuffix} - ${company}`,
    company,
    companyLogo: null,
    companyWebsite: `https://${company.toLowerCase().replace(/\s+/g, '')}.com`,
    location: getLocation(i, locations),
    remote: remoteVal,
    employmentType: 'Full-time',
    experienceLevel: expLevel,
    salaryMin: opts.salaryMin + i * 50000,
    salaryMax: opts.salaryMax + i * 100000,
    currency: 'INR',
    description: `${company} is hiring ${keyword} ${opts.titleSuffix}. Apply now for this opportunity.`,
    responsibilities: ['Work on assigned projects', 'Collaborate with teams', 'Attend training sessions', 'Complete deliverables on time'],
    requirements: ['Strong communication', 'Team player', 'Quick learner'],
    benefits: ['Health insurance', 'Performance bonus', 'Learning opportunities'],
    postedDate: new Date(now - i * 86400000).toISOString(),
    applicationDeadline: new Date(now + 30 * 86400000).toISOString(),
    easyApply: opts.alwaysEasyApply ?? true,
    tags: [keyword.toLowerCase(), providerId, company.toLowerCase()],
    metadata: { country: 'IN', source: providerId },
  }
}
