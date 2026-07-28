import { describe, it, expect } from 'vitest'
import { rankByMatch, rankByNewest, rankBySalary } from './ranking'
import type { MatchResult } from './types'

function makeMatch(id: string, overall: number, salary: number, date: string): MatchResult {
  return {
    jobId: id, overall, confidence: 0.5, decision: 'consider',
    skillScore: 0.5, skillDetail: { exactMatches: [], similarMatches: [], missingSkills: [], transferableSkills: [], totalJobSkills: 0, matchedCount: 0, coveragePercent: 0 },
    experienceScore: 0.5, experienceDetail: { userYears: 0, requiredYears: null, relevantExperience: false, titleMatch: false, leadershipMatch: false, domainMatch: false, score: 0.5 },
    educationScore: 0.5, educationDetail: { levelMatch: false, fieldMatch: false, userLevel: '', requiredLevel: null, userField: null, requiredField: null, score: 0.5 },
    salaryScore: 0.5, salaryDetail: { jobMin: null, jobMax: null, userMin: null, userMax: null, currency: null, marketAlignment: 'unknown', score: 0.5 },
    locationScore: 0.5, locationDetail: { remoteMatch: false, locationMatch: false, relocationRequired: false, remotePreference: null, jobRemote: '', score: 0.5 },
    resumeScore: 0.5, resumeDetail: { hasResume: false, resumeConfidence: 0, score: 0.5 },
    explanations: [], missingSkills: [], recommendedLearning: [], recommendedResumeId: null,
    scoredAt: new Date().toISOString(),
    job: {
      id, provider: 'linkedin', sourceUrl: '', externalId: '', title: 'Engineer', company: 'Co',
      companyLogo: null, companyWebsite: null, location: 'SF', country: 'US', remote: 'remote',
      employmentType: 'full_time', experienceLevel: null, salaryMin: salary, salaryMax: salary + 10000,
      currency: 'USD', description: '', responsibilities: [], requiredSkills: [], preferredSkills: [],
      benefits: [], visaSponsorship: null, postedDate: date, applicationDeadline: null,
      easyApply: false, tags: [], metadata: {}, normalizedTitle: 'engineer', normalizedCompany: 'co',
      freshnessScore: 0.5, discoveredAt: date,
    },
  }
}

describe('rankByMatch', () => {
  it('sorts by overall match descending', () => {
    const results = [makeMatch('a', 0.5, 0, ''), makeMatch('b', 0.9, 0, ''), makeMatch('c', 0.7, 0, '')]
    const ranked = rankByMatch(results)
    expect(ranked[0].overall).toBe(0.9)
    expect(ranked[1].overall).toBe(0.7)
    expect(ranked[2].overall).toBe(0.5)
  })
})

describe('rankByNewest', () => {
  it('sorts by date descending', () => {
    const results = [makeMatch('a', 0, 0, '2024-01-01'), makeMatch('b', 0, 0, '2024-06-01'), makeMatch('c', 0, 0, '2024-03-01')]
    const ranked = rankByNewest(results)
    expect(ranked[0].job.postedDate).toBe('2024-06-01')
    expect(ranked[1].job.postedDate).toBe('2024-03-01')
    expect(ranked[2].job.postedDate).toBe('2024-01-01')
  })
})

describe('rankBySalary', () => {
  it('sorts by salary descending', () => {
    const results = [makeMatch('a', 0, 50000, ''), makeMatch('b', 0, 150000, ''), makeMatch('c', 0, 100000, '')]
    const ranked = rankBySalary(results)
    expect(ranked[0].job.salaryMin).toBe(150000)
    expect(ranked[1].job.salaryMin).toBe(100000)
    expect(ranked[2].job.salaryMin).toBe(50000)
  })
})
