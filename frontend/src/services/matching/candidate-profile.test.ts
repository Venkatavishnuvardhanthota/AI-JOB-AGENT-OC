import { describe, it, expect } from 'vitest'
import { buildCandidateProfile, createDefaultProfile } from './candidate-profile'

describe('buildCandidateProfile', () => {
  it('builds a profile from input data', () => {
    const profile = buildCandidateProfile({
      headline: 'Senior Engineer',
      skills: [{ name: 'React', category: 'frontend', proficiency: 5 }],
      experience: [{ title: 'Engineer', company: 'Co', startDate: '2020-01-01', isCurrent: true }],
      education: [{ institution: 'MIT', degree: "Bachelor's", fieldOfStudy: 'CS' }],
    })
    expect(profile.headline).toBe('Senior Engineer')
    expect(profile.skills).toHaveLength(1)
    expect(profile.skills[0].name).toBe('React')
    expect(profile.experience).toHaveLength(1)
    expect(profile.education).toHaveLength(1)
    expect(profile.totalYearsOfExperience).toBeGreaterThan(0)
  })

  it('creates empty profile with defaults', () => {
    const profile = buildCandidateProfile({})
    expect(profile.skills).toHaveLength(0)
    expect(profile.experience).toHaveLength(0)
    expect(profile.totalYearsOfExperience).toBe(0)
  })
})

describe('createDefaultProfile', () => {
  it('returns a profile with all defaults', () => {
    const profile = createDefaultProfile()
    expect(profile.preferredRoles).toEqual([])
    expect(profile.skills).toEqual([])
    expect(profile.totalYearsOfExperience).toBe(0)
  })
})
