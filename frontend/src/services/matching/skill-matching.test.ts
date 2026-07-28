import { describe, it, expect } from 'vitest'
import { computeSkillMatch } from './skill-matching'
import type { CandidateProfile } from './types'
import type { Job } from '@/services/discovery/types'

function makeJob(overrides: Partial<Job> = {}): Job {
  return {
    id: '1', provider: 'linkedin', sourceUrl: '', externalId: 'ext_1',
    title: 'Engineer', company: 'Google', companyLogo: null, companyWebsite: null,
    location: 'SF', country: 'US', remote: 'remote', employmentType: 'full_time',
    experienceLevel: null, salaryMin: null, salaryMax: null, currency: null,
    description: '', responsibilities: [], benefits: [], visaSponsorship: null,
    postedDate: null, applicationDeadline: null, easyApply: false,
    tags: [], metadata: {}, normalizedTitle: 'engineer', normalizedCompany: 'google',
    freshnessScore: 0.5, discoveredAt: '', requiredSkills: [], preferredSkills: [],
    ...overrides,
  }
}

const profile: CandidateProfile = {
  preferredRoles: [], headline: null, bio: null, location: null,
  salaryExpectationMin: null, salaryExpectationMax: null, salaryCurrency: null,
  portfolioUrl: null, linkedinUrl: null, githubUrl: null,
  skills: [{ name: 'React', category: null, proficiency: 5 }, { name: 'TypeScript', category: null, proficiency: 4 }],
  experience: [], education: [], certifications: [], languages: [], projects: [],
  visaSponsorshipRequired: false, remotePreference: null, preferredLocations: [],
  employmentType: null, totalYearsOfExperience: 0,
}

describe('computeSkillMatch', () => {
  it('returns 100% when all skills match', () => {
    const job = makeJob({ requiredSkills: ['React', 'TypeScript'] })
    const result = computeSkillMatch(job, profile)
    expect(result.coveragePercent).toBe(100)
    expect(result.matchedCount).toBe(2)
    expect(result.missingSkills).toHaveLength(0)
  })

  it('detects missing skills', () => {
    const job = makeJob({ requiredSkills: ['React', 'Python', 'AWS'] })
    const result = computeSkillMatch(job, profile)
    expect(result.matchedCount).toBe(1)
    expect(result.missingSkills).toHaveLength(2)
  })

  it('handles empty job skills', () => {
    const job = makeJob({ requiredSkills: [] })
    const result = computeSkillMatch(job, profile)
    expect(result.coveragePercent).toBe(0)
  })
})
