import { describe, it, expect } from 'vitest'
import { deduplicate, countDuplicates } from './deduplication'
import type { Job, ProviderId } from './types'

function makeJob(id: string, title: string, company: string, location: string, provider: ProviderId = 'linkedin', externalId?: string): Job {
  return {
    id,
    provider,
    sourceUrl: `https://${provider}.com/jobs/${id}`,
    externalId: externalId || `ext_${id}`,
    title,
    company,
    companyLogo: null,
    companyWebsite: null,
    location,
    country: null,
    remote: 'remote',
    employmentType: 'full_time',
    experienceLevel: null,
    salaryMin: null,
    salaryMax: null,
    currency: null,
    description: '',
    responsibilities: [],
    requiredSkills: [],
    preferredSkills: [],
    benefits: [],
    visaSponsorship: null,
    postedDate: null,
    applicationDeadline: null,
    easyApply: false,
    tags: [],
    metadata: {},
    normalizedTitle: title.toLowerCase().replace(/[^a-z0-9\s]/g, '').trim(),
    normalizedCompany: company.toLowerCase().replace(/[^a-z0-9\s]/g, '').trim(),
    freshnessScore: 0.5,
    discoveredAt: new Date().toISOString(),
  }
}

describe('deduplicate', () => {
  it('returns all unique jobs when there are no duplicates', () => {
    const jobs = [
      makeJob('1', 'Software Engineer', 'Google', 'SF'),
      makeJob('2', 'Data Scientist', 'Meta', 'NYC'),
    ]
    const { unique, duplicates } = deduplicate(jobs)
    expect(unique).toHaveLength(2)
    expect(duplicates).toHaveLength(0)
  })

  it('detects exact duplicates by external id and provider', () => {
    const jobs = [
      makeJob('1', 'Engineer', 'Google', 'SF', 'linkedin', 'ext_1'),
      makeJob('2', 'Engineer', 'Google', 'SF', 'linkedin', 'ext_1'),
    ]
    const { unique, duplicates } = deduplicate(jobs)
    expect(unique).toHaveLength(1)
    expect(duplicates).toHaveLength(1)
  })

  it('detects duplicates by same title and company', () => {
    const jobs = [
      makeJob('1', 'Software Engineer', 'Google', 'San Francisco, CA'),
      makeJob('2', 'Software Engineer', 'Google', 'San Francisco, CA'),
    ]
    const { unique, duplicates } = deduplicate(jobs)
    expect(unique).toHaveLength(1)
    expect(duplicates).toHaveLength(1)
  })

  it('counts duplicates correctly', () => {
    const jobs = [
      makeJob('1', 'Engineer', 'Google', 'SF'),
      makeJob('2', 'Engineer', 'Google', 'SF'),
      makeJob('3', 'Designer', 'Figma', 'NYC'),
    ]
    expect(countDuplicates(jobs)).toBe(1)
  })
})
