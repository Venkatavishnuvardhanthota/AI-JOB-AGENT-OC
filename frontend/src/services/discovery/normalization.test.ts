import { describe, it, expect } from 'vitest'
import { normalizeTitle, normalizeCompany, normalizeJob, normalizeJobs, computeFreshness } from './normalization'
import type { RawJob } from './types'

describe('normalizeTitle', () => {
  it('normalizes common titles', () => {
    expect(normalizeTitle('Senior Software Engineer')).toBe('software engineer')
    expect(normalizeTitle('Frontend Developer')).toBe('frontend developer')
    expect(normalizeTitle('Full Stack Engineer')).toBe('full stack developer')
    expect(normalizeTitle('ML Engineer')).toBe('machine learning engineer')
  })

  it('handles empty strings', () => {
    expect(normalizeTitle('')).toBe('')
  })

  it('strips special characters', () => {
    expect(normalizeTitle('Software Engineer (Remote)')).toBe('software engineer')
  })
})

describe('normalizeCompany', () => {
  it('removes common suffixes', () => {
    expect(normalizeCompany('Google Inc')).toBe('google')
    expect(normalizeCompany('Microsoft Corporation')).toBe('microsoft')
    expect(normalizeCompany('Acme Technologies')).toBe('acme')
  })

  it('lowercases and trims', () => {
    expect(normalizeCompany('  ABC Corp  ')).toBe('abc')
  })
})

describe('computeFreshness', () => {
  it('returns 1.0 for today', () => {
    expect(computeFreshness(new Date().toISOString())).toBe(1.0)
  })

  it('returns 0.5 for missing date', () => {
    expect(computeFreshness(null)).toBe(0.5)
  })

  it('returns lower scores for older dates', () => {
    const oldDate = new Date(Date.now() - 90 * 86400000).toISOString()
    expect(computeFreshness(oldDate)).toBeLessThan(0.5)
  })
})

describe('normalizeJob', () => {
  const raw: RawJob = {
    externalId: 'test_123',
    title: 'Software Engineer',
    company: 'Test Corp',
    companyLogo: null,
    companyWebsite: null,
    location: 'San Francisco, CA',
    remote: 'Remote',
    employmentType: 'Full-time',
    experienceLevel: 'Senior',
    salaryMin: 100000,
    salaryMax: 150000,
    currency: 'USD',
    description: 'A great job',
    responsibilities: ['Code', 'Review'],
    requiredSkills: ['React', 'TypeScript'],
    preferredSkills: ['GraphQL'],
    benefits: ['Health'],
    visaSponsorship: true,
    postedDate: new Date().toISOString(),
    applicationDeadline: null,
    easyApply: true,
    tags: ['engineering'],
    metadata: { country: 'US' },
  }

  it('creates a normalized job from raw data', () => {
    const job = normalizeJob(raw, 'linkedin', 'https://linkedin.com/jobs/123')
    expect(job.id).toContain('job_linkedin')
    expect(job.title).toBe('Software Engineer')
    expect(job.normalizedTitle).toBe('software engineer')
    expect(job.normalizedCompany).toBe('test')
    expect(job.provider).toBe('linkedin')
    expect(job.remote).toBe('remote')
    expect(job.employmentType).toBe('full_time')
    expect(job.freshnessScore).toBe(1.0)
  })
})

describe('normalizeJobs', () => {
  it('normalizes multiple jobs', () => {
    const raws: RawJob[] = [
      { externalId: 'a', title: 'Engineer', company: 'Co', companyLogo: null, companyWebsite: null, location: 'NYC', remote: null, employmentType: null, experienceLevel: null, salaryMin: null, salaryMax: null, currency: null, description: '', responsibilities: [], requiredSkills: [], preferredSkills: [], benefits: [], visaSponsorship: null, postedDate: null, applicationDeadline: null, easyApply: false, tags: [], metadata: {} },
      { externalId: 'b', title: 'Developer', company: 'Co2', companyLogo: null, companyWebsite: null, location: 'SF', remote: null, employmentType: null, experienceLevel: null, salaryMin: null, salaryMax: null, currency: null, description: '', responsibilities: [], requiredSkills: [], preferredSkills: [], benefits: [], visaSponsorship: null, postedDate: null, applicationDeadline: null, easyApply: false, tags: [], metadata: {} },
    ]
    const jobs = normalizeJobs(raws, 'indeed', 'https://indeed.com')
    expect(jobs).toHaveLength(2)
    expect(jobs[0].provider).toBe('indeed')
    expect(jobs[1].provider).toBe('indeed')
  })
})
