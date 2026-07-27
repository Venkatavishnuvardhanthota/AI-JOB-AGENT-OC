import { describe, it, expect } from 'vitest'
import { computeExperienceMatch } from './experience-matching'
import type { CandidateProfile } from './types'
import type { Job } from '@/services/discovery/types'

function makeJob(overrides: Partial<Job> = {}): Job {
  return {
    id: '1', provider: 'linkedin', sourceUrl: '', externalId: 'ext_1',
    title: 'Senior Software Engineer', company: 'Co', companyLogo: null, companyWebsite: null,
    location: 'SF', country: 'US', remote: 'remote', employmentType: 'full_time',
    experienceLevel: null, salaryMin: null, salaryMax: null, currency: null,
    description: '5+ years of experience required', responsibilities: [], benefits: [],
    visaSponsorship: null, postedDate: null, applicationDeadline: null, easyApply: false,
    tags: [], metadata: {}, normalizedTitle: 'senior software engineer', normalizedCompany: 'co',
    freshnessScore: 0.5, discoveredAt: '', requiredSkills: [], preferredSkills: [],
    ...overrides,
  }
}

describe('computeExperienceMatch', () => {
  it('scores well when user has sufficient experience', () => {
    const profile: CandidateProfile = {
      preferredRoles: [], headline: null, bio: null, location: null,
      salaryExpectationMin: null, salaryExpectationMax: null, salaryCurrency: null,
      portfolioUrl: null, linkedinUrl: null, githubUrl: null,
      skills: [], experience: [
        { title: 'Software Engineer', company: 'Co', location: null, startDate: '2018-01-01', endDate: null, isCurrent: true, description: null },
      ], education: [], certifications: [], languages: [], projects: [],
      visaSponsorshipRequired: false, remotePreference: null, preferredLocations: [],
      employmentType: null, totalYearsOfExperience: 8,
    }
    const job = makeJob()
    const result = computeExperienceMatch(job, profile)
    expect(result.score).toBeGreaterThanOrEqual(0.7)
  })

  it('detects title match', () => {
    const profile: CandidateProfile = {
      preferredRoles: [], headline: null, bio: null, location: null,
      salaryExpectationMin: null, salaryExpectationMax: null, salaryCurrency: null,
      portfolioUrl: null, linkedinUrl: null, githubUrl: null,
      skills: [], experience: [
        { title: 'Senior Software Engineer', company: 'Co', location: null, startDate: null, endDate: null, isCurrent: false, description: null },
      ], education: [], certifications: [], languages: [], projects: [],
      visaSponsorshipRequired: false, remotePreference: null, preferredLocations: [],
      employmentType: null, totalYearsOfExperience: 5,
    }
    const job = makeJob()
    const result = computeExperienceMatch(job, profile)
    expect(result.titleMatch).toBe(true)
  })

  it('handles missing experience level', () => {
    const profile: CandidateProfile = {
      preferredRoles: [], headline: null, bio: null, location: null,
      salaryExpectationMin: null, salaryExpectationMax: null, salaryCurrency: null,
      portfolioUrl: null, linkedinUrl: null, githubUrl: null,
      skills: [], experience: [], education: [], certifications: [], languages: [], projects: [],
      visaSponsorshipRequired: false, remotePreference: null, preferredLocations: [],
      employmentType: null, totalYearsOfExperience: 0,
    }
    const job = makeJob()
    const result = computeExperienceMatch(job, profile)
    expect(result.score).toBeDefined()
    expect(result.userYears).toBe(0)
  })
})
