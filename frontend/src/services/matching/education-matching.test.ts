import { describe, it, expect } from 'vitest'
import { computeEducationMatch } from './education-matching'
import type { CandidateProfile } from './types'
import type { Job } from '@/services/discovery/types'

function makeJob(overrides: Partial<Job> = {}): Job {
  return {
    id: '1', provider: 'linkedin', sourceUrl: '', externalId: 'ext_1',
    title: 'Engineer', company: 'Co', companyLogo: null, companyWebsite: null,
    location: 'SF', country: 'US', remote: 'remote', employmentType: 'full_time',
    experienceLevel: null, salaryMin: null, salaryMax: null, currency: null,
    description: "Bachelor's degree in Computer Science", responsibilities: [],
    benefits: [], visaSponsorship: null, postedDate: null, applicationDeadline: null,
    easyApply: false, tags: [], metadata: {}, normalizedTitle: 'engineer',
    normalizedCompany: 'co', freshnessScore: 0.5, discoveredAt: '',
    requiredSkills: [], preferredSkills: [],
    ...overrides,
  }
}

describe('computeEducationMatch', () => {
  it('scores well when education matches', () => {
    const profile: CandidateProfile = {
      preferredRoles: [], headline: null, bio: null, location: null,
      salaryExpectationMin: null, salaryExpectationMax: null, salaryCurrency: null,
      portfolioUrl: null, linkedinUrl: null, githubUrl: null,
      skills: [], experience: [], certifications: [], languages: [], projects: [],
      education: [{ institution: 'MIT', degree: "Bachelor's", fieldOfStudy: 'Computer Science', startDate: null, endDate: null, gpa: null }],
      visaSponsorshipRequired: false, remotePreference: null, preferredLocations: [],
      employmentType: null, totalYearsOfExperience: 0,
    }
    const job = makeJob()
    const result = computeEducationMatch(job, profile)
    expect(result.levelMatch).toBe(true)
    expect(result.fieldMatch).toBe(true)
  })

  it('handles no education requirement', () => {
    const profile: CandidateProfile = {
      preferredRoles: [], headline: null, bio: null, location: null,
      salaryExpectationMin: null, salaryExpectationMax: null, salaryCurrency: null,
      portfolioUrl: null, linkedinUrl: null, githubUrl: null,
      skills: [], experience: [], certifications: [], languages: [], projects: [],
      education: [{ institution: 'MIT', degree: "Bachelor's", fieldOfStudy: 'CS', startDate: null, endDate: null, gpa: null }],
      visaSponsorshipRequired: false, remotePreference: null, preferredLocations: [],
      employmentType: null, totalYearsOfExperience: 0,
    }
    const job = makeJob({ description: 'No specific degree required' })
    const result = computeEducationMatch(job, profile)
    expect(result.score).toBeGreaterThanOrEqual(0.7)
  })
})
