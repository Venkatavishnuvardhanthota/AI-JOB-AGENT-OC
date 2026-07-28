import type { ResumeMatchDetail } from './types'
import type { CandidateProfile } from './types'
import type { Job } from '@/services/discovery/types'

export function computeResumeMatch(job: Job, profile: CandidateProfile, hasResume: boolean): ResumeMatchDetail {
  if (!hasResume) {
    return { hasResume: false, resumeConfidence: 0, score: 0.2 }
  }

  const hasRelevantProjects = profile.projects.some(p => {
    if (!p.description) return false
    const desc = p.description.toLowerCase()
    const jobSkills = [...job.requiredSkills, ...job.preferredSkills]
    return jobSkills.some(s => desc.includes(s.toLowerCase()))
  })

  const hasRelevantExperience = profile.experience.some(exp => {
    const titleLower = exp.title.toLowerCase()
    const jobTitleLower = job.title.toLowerCase()
    return titleLower.includes(jobTitleLower) || jobTitleLower.includes(titleLower)
  })

  let confidence = 0.5
  if (hasRelevantProjects) confidence += 0.2
  if (hasRelevantExperience) confidence += 0.2
  if (profile.skills.length > 10) confidence += 0.1

  const totalJobSkills = job.requiredSkills.length + job.preferredSkills.length
  const matchedSkills = job.requiredSkills.filter(js =>
    profile.skills.some(us => us.name.toLowerCase() === js.toLowerCase())
  ).length
  const skillCoverage = totalJobSkills > 0 ? matchedSkills / totalJobSkills : 0

  if (skillCoverage > 0.5) confidence += 0.1

  confidence = Math.min(1, Math.round(confidence * 100) / 100)

  let score = 0
  if (confidence >= 0.8) score = 1.0
  else if (confidence >= 0.6) score = 0.8
  else if (confidence >= 0.4) score = 0.6
  else score = 0.4

  return {
    hasResume: true,
    resumeConfidence: confidence,
    score,
  }
}

export function selectBestResume(resumes: { id: string; skills: string[]; title?: string }[], job: Job): string | null {
  if (resumes.length === 0) return null

  let bestId: string | null = null
  let bestScore = -1

  for (const resume of resumes) {
    const jobSkills = new Set([...job.requiredSkills, ...job.preferredSkills].map(s => s.toLowerCase()))
    const resumeSkills = new Set(resume.skills.map(s => s.toLowerCase()))
    const intersection = new Set([...jobSkills].filter(s => resumeSkills.has(s)))
    const score = jobSkills.size > 0 ? intersection.size / jobSkills.size : 0

    if (score > bestScore) {
      bestScore = score
      bestId = resume.id
    }
  }

  return bestId
}
