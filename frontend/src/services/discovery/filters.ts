import type { Job, DiscoveryFilters, ProviderId } from './types'

export function applyFilters(jobs: Job[], filters: DiscoveryFilters): Job[] {
  return jobs.filter(job => {
    if (filters.providers.length > 0 && !filters.providers.includes(job.provider)) return false
    if (filters.companies.length > 0 && !filters.companies.some(c => job.normalizedCompany.includes(c.toLowerCase()))) return false
    if (filters.locations.length > 0 && !filters.locations.some(l => job.location.toLowerCase().includes(l.toLowerCase()))) return false
    if (filters.remote && job.remote !== filters.remote && filters.remote !== 'any') return false
    if (filters.salaryMin !== null && job.salaryMax !== null && job.salaryMax < filters.salaryMin) return false
    if (filters.salaryMax !== null && job.salaryMin !== null && job.salaryMin > filters.salaryMax) return false
    if (filters.experienceLevel && job.experienceLevel !== filters.experienceLevel) return false
    if (filters.employmentType && job.employmentType !== filters.employmentType) return false
    if (filters.skills.length > 0 && !filters.skills.some(s => job.requiredSkills.some(rs => rs.toLowerCase().includes(s.toLowerCase())))) return false
    if (filters.postedWithinDays !== null && job.postedDate) {
      const posted = new Date(job.postedDate).getTime()
      const cutoff = Date.now() - filters.postedWithinDays * 86400000
      if (posted < cutoff) return false
    }
    if (filters.easyApplyOnly && !job.easyApply) return false
    if (filters.tags.length > 0 && !filters.tags.some(t => job.tags.some(jt => jt.toLowerCase().includes(t.toLowerCase())))) return false
    return true
  })
}

export function extractFilterOptions(jobs: Job[]): {
  providers: ProviderId[]
  companies: string[]
  locations: string[]
  skills: string[]
  tags: string[]
} {
  const providerSet = new Set<ProviderId>()
  const companySet = new Set<string>()
  const locationSet = new Set<string>()
  const skillSet = new Set<string>()
  const tagSet = new Set<string>()

  for (const job of jobs) {
    providerSet.add(job.provider)
    companySet.add(job.company)
    locationSet.add(job.location)
    for (const skill of job.requiredSkills) skillSet.add(skill)
    for (const tag of job.tags) tagSet.add(tag)
  }

  return {
    providers: [...providerSet],
    companies: [...companySet].sort(),
    locations: [...locationSet].sort(),
    skills: [...skillSet].sort(),
    tags: [...tagSet].sort(),
  }
}
