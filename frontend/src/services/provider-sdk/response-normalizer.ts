import type { RawJob } from '../discovery/types'
import { normalizeJob, normalizeJobs } from '../discovery/normalization'
import type { NormalizedResponse } from './types'
import type { ProviderId } from '../discovery/types'
import { ValidationError } from './errors'

interface ProviderSpecificJob {
  externalId: string
  title: string
  company: string
  companyLogo?: string | null
  companyWebsite?: string | null
  location: string
  remote?: string | null
  employmentType?: string | null
  experienceLevel?: string | null
  salaryMin?: number | null
  salaryMax?: number | null
  currency?: string | null
  description: string
  responsibilities?: string[]
  requiredSkills?: string[]
  preferredSkills?: string[]
  benefits?: string[]
  visaSponsorship?: boolean | null
  postedDate?: string | null
  applicationDeadline?: string | null
  easyApply?: boolean
  tags?: string[]
  metadata?: Record<string, unknown>
}

function validateRawJob(raw: ProviderSpecificJob, providerId: string): void {
  if (!raw.externalId) throw new ValidationError('Missing externalId', providerId, 'externalId')
  if (!raw.title) throw new ValidationError('Missing title', providerId, 'title')
  if (!raw.company) throw new ValidationError('Missing company', providerId, 'company')
  if (!raw.location && raw.location !== '') throw new ValidationError('Missing location', providerId, 'location')
  if (!raw.description) throw new ValidationError('Missing description', providerId, 'description')
}

function toRawJob(raw: ProviderSpecificJob): RawJob {
  return {
    externalId: raw.externalId,
    title: raw.title,
    company: raw.company,
    companyLogo: raw.companyLogo ?? null,
    companyWebsite: raw.companyWebsite ?? null,
    location: raw.location,
    remote: raw.remote ?? null,
    employmentType: raw.employmentType ?? null,
    experienceLevel: raw.experienceLevel ?? null,
    salaryMin: raw.salaryMin ?? null,
    salaryMax: raw.salaryMax ?? null,
    currency: raw.currency ?? null,
    description: raw.description,
    responsibilities: raw.responsibilities ?? [],
    requiredSkills: raw.requiredSkills ?? [],
    preferredSkills: raw.preferredSkills ?? [],
    benefits: raw.benefits ?? [],
    visaSponsorship: raw.visaSponsorship ?? null,
    postedDate: raw.postedDate ?? null,
    applicationDeadline: raw.applicationDeadline ?? null,
    easyApply: raw.easyApply ?? false,
    tags: raw.tags ?? [],
    metadata: raw.metadata ?? {},
  }
}

export const responseNormalizer = {
  normalizeOne(raw: ProviderSpecificJob, providerId: string, sourceUrl: string) {
    validateRawJob(raw, providerId)
    return normalizeJob(toRawJob(raw), providerId as ProviderId, sourceUrl)
  },

  normalizeMany(raws: ProviderSpecificJob[], providerId: string, sourceUrl: string) {
    for (const raw of raws) validateRawJob(raw, providerId)
    return normalizeJobs(raws.map(toRawJob), providerId as ProviderId, sourceUrl)
  },

  normalizeResponse<T extends ProviderSpecificJob>(
    response: { data: T[]; total?: number; hasMore?: boolean; cursor?: string },
    providerId: string,
    sourceUrl: string
  ): NormalizedResponse<ReturnType<typeof normalizeJob>> {
    const normalized = this.normalizeMany(response.data, providerId, sourceUrl)
    return {
      data: normalized,
      total: response.total ?? normalized.length,
      hasMore: response.hasMore ?? false,
      cursor: response.cursor,
    }
  },
}
