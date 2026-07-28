import type { SearchParams, RawJob } from '../discovery/types'

export interface PortalProviderConfig {
  id: string
  name: string
  description: string
  priority: number
  version: string
  capabilities: string[]
  baseUrl?: string
  searchEndpoint?: string
  jobDetailsEndpoint?: string
  defaultParams?: Record<string, string>
  headers?: Record<string, string>
  rateLimitPerSecond?: number
  timeoutMs?: number
  mockOptions: PortalMockOptions
}

export interface PortalMockOptions {
  companies: string[]
  count: number
  titleSuffix: string
  salaryMin: number
  salaryMax: number
  locations?: string[]
  alwaysEasyApply?: boolean
  remoteMod?: number
  expLevels?: string[]
}

export interface PortalInternshipFields {
  duration?: string
  stipend?: string
  startDate?: string
  applyBy?: string
  internshipType?: string
}

export interface PortalFresherFields {
  trainingPeriod?: string
  bondYears?: number
  batchYear?: number
  placementGuarantee?: boolean
}

export interface PortalCompetitionFields {
  prize?: string
  teamSize?: number
  deadline?: string
  format?: string
}

export interface PortalJobRaw {
  externalId: string
  title: string
  company: string
  location: string
  description: string
  employmentType?: string
  experienceLevel?: string
  salaryMin?: number | null
  salaryMax?: number | null
  currency?: string
  postedDate?: string
  applicationDeadline?: string | null
  easyApply?: boolean
  remote?: string
  companyLogo?: string | null
  companyWebsite?: string | null
  requirements?: string[]
  responsibilities?: string[]
  skills?: string[]
  benefits?: string[]
  tags?: string[]
  metadata?: Record<string, unknown>
}

export function normalizePortalJob(job: PortalJobRaw, providerId: string): RawJob {
  return {
    externalId: job.externalId,
    title: job.title,
    company: job.company,
    companyLogo: job.companyLogo ?? null,
    companyWebsite: job.companyWebsite ?? null,
    location: job.location,
    remote: job.remote ?? null,
    employmentType: job.employmentType ?? null,
    experienceLevel: job.experienceLevel ?? null,
    salaryMin: job.salaryMin ?? null,
    salaryMax: job.salaryMax ?? null,
    currency: job.currency ?? 'INR',
    description: job.description,
    responsibilities: job.responsibilities ?? [],
    requiredSkills: job.requirements ?? job.skills ?? [],
    preferredSkills: [],
    benefits: job.benefits ?? [],
    visaSponsorship: null,
    postedDate: job.postedDate ?? null,
    applicationDeadline: job.applicationDeadline ?? null,
    easyApply: job.easyApply ?? false,
    tags: job.tags ?? [providerId],
    metadata: { ...job.metadata, portalProvider: providerId },
  }
}
