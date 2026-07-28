import { describe, it, expect } from 'vitest'
import { computeLocationMatch } from './location-matching'
import type { CandidateProfile } from './types'
import type { Job } from '@/services/discovery/types'

function makeJob(overrides: Partial<Job> = {}): Job {
  return {
    id: '1', provider: 'linkedin', sourceUrl: '', externalId: 'ext_1',
    title: 'Engineer', company: 'Co', companyLogo: null, companyWebsite: null,
    location: 'San Francisco, CA', country: 'US', remote: 'remote',
    employmentType: 'full_time', experienceLevel: null, salaryMin: null, salaryMax: null,
    currency: null, description: '', responsibilities: [], benefits: [],
    visaSponsorship: null, postedDate: null, applicationDeadline: null, easyApply: false,
    tags: [], metadata: {}, normalizedTitle: 'engineer', normalizedCompany: 'co',
    freshnessScore: 0.5, discoveredAt: '', requiredSkills: [], preferredSkills: [],
    ...overrides,
  }
}

describe('computeLocationMatch', () => {
  it('scores 1.0 for remote jobs', () => {
    const profile: CandidateProfile = {
      preferredRoles: [], headline: null, bio: null, location: 'NYC',
      salaryExpectationMin: null, salaryExpectationMax: null, salaryCurrency: null,
      portfolioUrl: null, linkedinUrl: null, githubUrl: null,
      skills: [], experience: [], education: [], certifications: [], languages: [], projects: [],
      visaSponsorshipRequired: false, remotePreference: 'remote', preferredLocations: [],
      employmentType: null, totalYearsOfExperience: 0,
    }
    const job = makeJob({ remote: 'remote', location: 'Remote' })
    const result = computeLocationMatch(job, profile)
    expect(result.remoteMatch).toBe(true)
    expect(result.score).toBe(1.0)
  })

  it('handles location match', () => {
    const profile: CandidateProfile = {
      preferredRoles: [], headline: null, bio: null, location: 'San Francisco',
      salaryExpectationMin: null, salaryExpectationMax: null, salaryCurrency: null,
      portfolioUrl: null, linkedinUrl: null, githubUrl: null,
      skills: [], experience: [], education: [], certifications: [], languages: [], projects: [],
      visaSponsorshipRequired: false, remotePreference: null, preferredLocations: [],
      employmentType: null, totalYearsOfExperience: 0,
    }
    const job = makeJob({ remote: 'onsite', location: 'San Francisco, CA' })
    const result = computeLocationMatch(job, profile)
    expect(result.locationMatch).toBe(true)
    expect(result.relocationRequired).toBe(false)
  })

  it('detects relocation required', () => {
    const profile: CandidateProfile = {
      preferredRoles: [], headline: null, bio: null, location: 'New York',
      salaryExpectationMin: null, salaryExpectationMax: null, salaryCurrency: null,
      portfolioUrl: null, linkedinUrl: null, githubUrl: null,
      skills: [], experience: [], education: [], certifications: [], languages: [], projects: [],
      visaSponsorshipRequired: false, remotePreference: null, preferredLocations: [],
      employmentType: null, totalYearsOfExperience: 0,
    }
    const job = makeJob({ remote: 'onsite', location: 'San Francisco, CA' })
    const result = computeLocationMatch(job, profile)
    expect(result.relocationRequired).toBe(true)
  })
})
