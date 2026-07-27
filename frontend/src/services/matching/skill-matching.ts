import type { SkillMatchDetail } from './types'
import type { CandidateProfile } from './types'
import type { Job } from '@/services/discovery/types'
import { findMatchingSkills } from './skill-synonyms'

export function computeSkillMatch(job: Job, profile: CandidateProfile): SkillMatchDetail {
  const jobSkills = [...job.requiredSkills, ...job.preferredSkills]
  const userSkills = profile.skills.map(s => s.name)

  const { exact, similar, missing, transferable } = findMatchingSkills(userSkills, jobSkills)

  const totalJobSkills = jobSkills.length || 1
  const matchedCount = exact.length
  const coveragePercent = Math.round((matchedCount / totalJobSkills) * 100)

  return {
    exactMatches: exact,
    similarMatches: similar,
    missingSkills: missing,
    transferableSkills: transferable,
    totalJobSkills,
    matchedCount,
    coveragePercent,
  }
}
