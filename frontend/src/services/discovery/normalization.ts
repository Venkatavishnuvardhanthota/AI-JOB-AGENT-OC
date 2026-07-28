import type { Job, RawJob, EmploymentType, ExperienceLevel, RemotePreference, ProviderId } from './types'

const JOB_TITLE_NORMALIZATION: Record<string, string> = {
  'software engineer': 'software engineer',
  'software developer': 'software engineer',
  'full stack': 'full stack developer',
  'fullstack': 'full stack developer',
  'frontend': 'frontend developer',
  'front end': 'frontend developer',
  'backend': 'backend developer',
  'back end': 'backend developer',
  'data scientist': 'data scientist',
  'ml engineer': 'machine learning engineer',
  'machine learning engineer': 'machine learning engineer',
  'devops': 'devops engineer',
  'sre': 'site reliability engineer',
  'product manager': 'product manager',
  'qa engineer': 'qa engineer',
  'quality assurance': 'qa engineer',
  'engineering manager': 'engineering manager',
  'tech lead': 'tech lead',
  'principal engineer': 'principal engineer',
  'staff engineer': 'staff engineer',
  'data engineer': 'data engineer',
  'data analyst': 'data analyst',
  'ai engineer': 'ai engineer',
  'ai ml engineer': 'ai engineer',
  'cloud engineer': 'cloud engineer',
  'security engineer': 'security engineer',
  'systems engineer': 'systems engineer',
  'network engineer': 'network engineer',
  'designer': 'designer',
  'ux designer': 'ux designer',
  'ui designer': 'ui designer',
  'ui ux designer': 'ux designer',
  'solution architect': 'solution architect',
  'software architect': 'software architect',
}

const COMPANY_SUFFIXES = ['inc', 'llc', 'ltd', 'limited', 'corp', 'corporation', 'pvt', 'private', 'technologies', 'technology', 'tech', 'solutions', 'software', 'group', 'holdings', 'international', 'global', 'services']

export function normalizeTitle(title: string): string {
  const lower = title.toLowerCase().trim()
  for (const [pattern, normalized] of Object.entries(JOB_TITLE_NORMALIZATION)) {
    if (lower.includes(pattern)) return normalized
  }
  return lower.replace(/[^a-z0-9\s]/g, '').replace(/\s+/g, ' ').trim()
}

export function normalizeCompany(company: string): string {
  let normalized = company.toLowerCase().trim()
  for (const suffix of COMPANY_SUFFIXES) {
    const regex = new RegExp(`\\b${suffix}\\.?$`, 'i')
    normalized = normalized.replace(regex, '').trim()
  }
  return normalized.replace(/[^a-z0-9\s]/g, '').replace(/\s+/g, ' ').trim()
}

function detectEmploymentType(raw: string | null): EmploymentType {
  if (!raw) return 'full_time'
  const lower = raw.toLowerCase()
  if (lower.includes('part')) return 'part_time'
  if (lower.includes('contract') || lower.includes('temporary')) return 'contract'
  if (lower.includes('intern')) return 'internship'
  if (lower.includes('volunteer')) return 'volunteer'
  if (lower.includes('freelance')) return 'freelance'
  return 'full_time'
}

function detectExperienceLevel(raw: string | null): ExperienceLevel | null {
  if (!raw) return null
  const lower = raw.toLowerCase()
  if (lower.includes('intern') || lower.includes('fresher')) return 'internship'
  if (lower.includes('entry') || lower.includes('junior') || lower.includes('0-')) return 'entry'
  if (lower.includes('associate') || lower.includes('1-') || lower.includes('2-')) return 'associate'
  if (lower.includes('mid') || lower.includes('senior') || lower.includes('3-') || lower.includes('4-') || lower.includes('5-')) return 'mid_senior'
  if (lower.includes('director') || lower.includes('head')) return 'director'
  if (lower.includes('executive') || lower.includes('vp') || lower.includes('chief')) return 'executive'
  return null
}

function detectRemote(raw: string | null): RemotePreference {
  if (!raw) return 'onsite'
  const lower = raw.toLowerCase()
  if (lower.includes('remote') || lower === 'yes') return 'remote'
  if (lower.includes('hybrid')) return 'hybrid'
  return 'onsite'
}

let jobCounter = 0

export function normalizeJob(raw: RawJob, provider: ProviderId, sourceUrl: string): Job {
  jobCounter++
  const now = new Date().toISOString()
  return {
    id: `job_${provider}_${raw.externalId}_${Date.now()}_${jobCounter}`,
    provider,
    sourceUrl,
    externalId: raw.externalId,
    title: raw.title,
    company: raw.company,
    companyLogo: raw.companyLogo,
    companyWebsite: raw.companyWebsite,
    location: raw.location,
    country: raw.metadata?.country as string | null ?? null,
    remote: detectRemote(raw.remote),
    employmentType: detectEmploymentType(raw.employmentType),
    experienceLevel: detectExperienceLevel(raw.experienceLevel),
    salaryMin: raw.salaryMin,
    salaryMax: raw.salaryMax,
    currency: raw.currency,
    description: raw.description,
    responsibilities: raw.responsibilities ?? [],
    requiredSkills: raw.requiredSkills ?? [],
    preferredSkills: raw.preferredSkills ?? [],
    benefits: raw.benefits ?? [],
    visaSponsorship: raw.visaSponsorship,
    postedDate: raw.postedDate,
    applicationDeadline: raw.applicationDeadline,
    easyApply: raw.easyApply,
    tags: raw.tags ?? [],
    metadata: raw.metadata ?? {},
    normalizedTitle: normalizeTitle(raw.title),
    normalizedCompany: normalizeCompany(raw.company),
    freshnessScore: computeFreshness(raw.postedDate),
    discoveredAt: now,
  }
}

export function computeFreshness(postedDate: string | null): number {
  if (!postedDate) return 0.5
  const posted = new Date(postedDate).getTime()
  const now = Date.now()
  const daysSincePosted = (now - posted) / 86400000
  if (daysSincePosted < 1) return 1.0
  if (daysSincePosted < 3) return 0.95
  if (daysSincePosted < 7) return 0.85
  if (daysSincePosted < 14) return 0.7
  if (daysSincePosted < 30) return 0.5
  if (daysSincePosted < 60) return 0.3
  return 0.1
}

export function normalizeJobs(rawJobs: RawJob[], provider: ProviderId, sourceUrl: string): Job[] {
  return rawJobs.map(raw => normalizeJob(raw, provider, sourceUrl))
}
