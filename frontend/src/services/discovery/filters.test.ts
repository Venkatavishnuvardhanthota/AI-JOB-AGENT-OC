import { describe, it, expect } from 'vitest'
import { applyFilters, extractFilterOptions } from './filters'
import type { Job, DiscoveryFilters } from './types'

function makeJob(overrides: Partial<Job> = {}): Job {
  return {
    id: '1', provider: 'linkedin', sourceUrl: '', externalId: 'ext_1',
    title: 'Engineer', company: 'Google', companyLogo: null, companyWebsite: null,
    location: 'San Francisco, CA', country: 'US', remote: 'remote',
    employmentType: 'full_time', experienceLevel: 'mid_senior',
    salaryMin: 100000, salaryMax: 150000, currency: 'USD',
    description: '', responsibilities: [], requiredSkills: ['React'],
    preferredSkills: [], benefits: [], visaSponsorship: true,
    postedDate: new Date().toISOString(), applicationDeadline: null,
    easyApply: true, tags: ['engineering'], metadata: {},
    normalizedTitle: 'engineer', normalizedCompany: 'google',
    freshnessScore: 0.9, discoveredAt: new Date().toISOString(),
    ...overrides,
  }
}

describe('applyFilters', () => {
  const jobs = [
    makeJob({ id: '1', provider: 'linkedin', remote: 'remote', salaryMin: 100000, salaryMax: 150000, employmentType: 'full_time', experienceLevel: 'mid_senior', easyApply: true, requiredSkills: ['React', 'TypeScript'] }),
    makeJob({ id: '2', provider: 'indeed', remote: 'onsite', salaryMin: 80000, salaryMax: 120000, employmentType: 'contract', experienceLevel: 'associate', easyApply: false, requiredSkills: ['Java'] }),
    makeJob({ id: '3', provider: 'linkedin', remote: 'remote', salaryMin: 200000, salaryMax: 300000, employmentType: 'full_time', experienceLevel: 'director', easyApply: true, requiredSkills: ['React', 'AWS'] }),
  ]

  it('returns all jobs with empty filters', () => {
    const filters: DiscoveryFilters = { providers: [], companies: [], locations: [], remote: null, salaryMin: null, salaryMax: null, experienceLevel: null, employmentType: null, skills: [], postedWithinDays: null, easyApplyOnly: false, tags: [] }
    expect(applyFilters(jobs, filters)).toHaveLength(3)
  })

  it('filters by provider', () => {
    const filters: DiscoveryFilters = { providers: ['indeed'], companies: [], locations: [], remote: null, salaryMin: null, salaryMax: null, experienceLevel: null, employmentType: null, skills: [], postedWithinDays: null, easyApplyOnly: false, tags: [] }
    const filtered = applyFilters(jobs, filters)
    expect(filtered).toHaveLength(1)
    expect(filtered[0].id).toBe('2')
  })

  it('filters by remote', () => {
    const filters: DiscoveryFilters = { providers: [], companies: [], locations: [], remote: 'remote', salaryMin: null, salaryMax: null, experienceLevel: null, employmentType: null, skills: [], postedWithinDays: null, easyApplyOnly: false, tags: [] }
    expect(applyFilters(jobs, filters)).toHaveLength(2)
  })

  it('filters by experience', () => {
    const filters: DiscoveryFilters = { providers: [], companies: [], locations: [], remote: null, salaryMin: null, salaryMax: null, experienceLevel: 'associate', employmentType: null, skills: [], postedWithinDays: null, easyApplyOnly: false, tags: [] }
    expect(applyFilters(jobs, filters)).toHaveLength(1)
  })

  it('filters by salary range', () => {
    const filters: DiscoveryFilters = { providers: [], companies: [], locations: [], remote: null, salaryMin: 150000, salaryMax: null, experienceLevel: null, employmentType: null, skills: [], postedWithinDays: null, easyApplyOnly: false, tags: [] }
    expect(applyFilters(jobs, filters)).toHaveLength(2)
  })

  it('filters by easy apply', () => {
    const filters: DiscoveryFilters = { providers: [], companies: [], locations: [], remote: null, salaryMin: null, salaryMax: null, experienceLevel: null, employmentType: null, skills: [], postedWithinDays: null, easyApplyOnly: true, tags: [] }
    expect(applyFilters(jobs, filters)).toHaveLength(2)
  })

  it('filters by skills', () => {
    const filters: DiscoveryFilters = { providers: [], companies: [], locations: [], remote: null, salaryMin: null, salaryMax: null, experienceLevel: null, employmentType: null, skills: ['Java'], postedWithinDays: null, easyApplyOnly: false, tags: [] }
    expect(applyFilters(jobs, filters)).toHaveLength(1)
  })
})

describe('extractFilterOptions', () => {
  it('extracts unique options from jobs', () => {
    const jobs = [
      makeJob({ provider: 'linkedin', company: 'Google', location: 'SF', tags: ['eng'], requiredSkills: ['React'] }),
      makeJob({ provider: 'indeed', company: 'Meta', location: 'NYC', tags: ['eng'], requiredSkills: ['React'] }),
    ]
    const options = extractFilterOptions(jobs)
    expect(options.providers).toHaveLength(2)
    expect(options.companies).toHaveLength(2)
    expect(options.locations).toHaveLength(2)
    expect(options.skills).toHaveLength(1)
    expect(options.tags).toHaveLength(1)
  })
})
