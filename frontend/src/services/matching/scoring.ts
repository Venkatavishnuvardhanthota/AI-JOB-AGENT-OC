import type { MatchResult, MatchWeights, MatchExplanation, SkillMatchDetail, ExperienceMatchDetail, EducationMatchDetail, SalaryMatchDetail, LocationMatchDetail, ResumeMatchDetail } from './types'
import { DEFAULT_MATCH_WEIGHTS } from './types'
import type { CandidateProfile } from './types'
import type { Job } from '@/services/discovery/types'
import { computeSkillMatch } from './skill-matching'
import { computeExperienceMatch } from './experience-matching'
import { computeEducationMatch } from './education-matching'
import { computeSalaryMatch } from './salary-matching'
import { computeLocationMatch } from './location-matching'
import { computeResumeMatch } from './resume-intelligence'
import { makeDecision } from './decision-engine'
import { generateSkillGapAnalysis } from './gap-analysis'

export function scoreJob(job: Job, profile: CandidateProfile, resumeId: string | null, weights: MatchWeights = DEFAULT_MATCH_WEIGHTS): MatchResult {
  const skillMatch = computeSkillMatch(job, profile)
  const experienceMatch = computeExperienceMatch(job, profile)
  const educationMatch = computeEducationMatch(job, profile)
  const salaryMatch = computeSalaryMatch(job, profile)
  const locationMatch = computeLocationMatch(job, profile)
  const resumeMatch = computeResumeMatch(job, profile, resumeId !== null)

  const skillScore = skillMatch.coveragePercent / 100
  const experienceScore = experienceMatch.score
  const educationScore = educationMatch.score
  const salaryScore = salaryMatch.score
  const locationScore = locationMatch.score
  const resumeScore = resumeMatch.score

  const projectScore = computeProjectScore(job, profile)
  const certScore = computeCertificationScore(job, profile)

  const totalWeight = weights.skill + weights.experience + weights.education +
    weights.salary + weights.location + weights.resume +
    weights.projects + weights.certifications

  const overall =
    (skillScore * weights.skill +
     experienceScore * weights.experience +
     educationScore * weights.education +
     salaryScore * weights.salary +
     locationScore * weights.location +
     resumeScore * weights.resume +
     projectScore * weights.projects +
     certScore * weights.certifications) / totalWeight

  const explanation: MatchExplanation[] = [
    buildExplanation('Skills', skillScore, weights.skill, skillMatch),
    buildExplanation('Experience', experienceScore, weights.experience, experienceMatch),
    buildExplanation('Education', educationScore, weights.education, educationMatch),
    buildExplanation('Salary', salaryScore, weights.salary, salaryMatch),
    buildExplanation('Location', locationScore, weights.location, locationMatch),
    buildExplanation('Resume', resumeScore, weights.resume, resumeMatch),
  ]

  const confidence = computeConfidence(skillScore, experienceScore, educationScore, salaryScore, locationScore)

  const decision = makeDecision(overall, confidence, skillScore, resumeMatch.hasResume)
  const gapAnalysis = generateSkillGapAnalysis(skillMatch, job)

  return {
    jobId: job.id,
    job,
    overall: Math.round(overall * 1000) / 1000,
    confidence: Math.round(confidence * 1000) / 1000,
    decision,
    skillScore: Math.round(skillScore * 1000) / 1000,
    skillDetail: skillMatch,
    experienceScore: Math.round(experienceScore * 1000) / 1000,
    experienceDetail: experienceMatch,
    educationScore: Math.round(educationScore * 1000) / 1000,
    educationDetail: educationMatch,
    salaryScore: Math.round(salaryScore * 1000) / 1000,
    salaryDetail: salaryMatch,
    locationScore: Math.round(locationScore * 1000) / 1000,
    locationDetail: locationMatch,
    resumeScore: Math.round(resumeScore * 1000) / 1000,
    resumeDetail: resumeMatch,
    explanations: explanation,
    missingSkills: gapAnalysis.missingSkills,
    recommendedLearning: gapAnalysis.recommendedLearning.map(r => r.skill),
    recommendedResumeId: resumeId,
    scoredAt: new Date().toISOString(),
  }
}

function computeProjectScore(job: Job, profile: CandidateProfile): number {
  if (profile.projects.length === 0) return 0.3
  const relevantProjects = profile.projects.filter(p => {
    if (!p.description) return false
    const desc = p.description.toLowerCase()
    return [...job.requiredSkills, ...job.preferredSkills].some(s => desc.includes(s.toLowerCase()))
  })
  return Math.min(1, 0.3 + relevantProjects.length * 0.15)
}

function computeCertificationScore(job: Job, profile: CandidateProfile): number {
  if (profile.certifications.length === 0) return 0.3
  const jobText = `${job.title} ${job.description}`.toLowerCase()
  const relevant = profile.certifications.filter(c => jobText.includes(c.name.toLowerCase()))
  return Math.min(1, 0.3 + relevant.length * 0.2)
}

function computeConfidence(skill: number, experience: number, education: number, salary: number, location: number): number {
  const components = [skill, experience, education, salary, location]
  const known = components.filter(s => s > 0)
  if (known.length === 0) return 0.3
  const avg = known.reduce((sum, s) => sum + s, 0) / known.length
  const completeness = known.length / components.length
  return avg * completeness
}

function buildExplanation(category: string, score: number, weight: number, detail: SkillMatchDetail | ExperienceMatchDetail | EducationMatchDetail | SalaryMatchDetail | LocationMatchDetail | ResumeMatchDetail): MatchExplanation {
  let details = ''
  let resultType: 'positive' | 'negative' | 'neutral' = 'neutral'

  if ('coveragePercent' in detail) {
    const d = detail as SkillMatchDetail
    details = `Matched ${d.matchedCount} of ${d.totalJobSkills} required skills (${d.coveragePercent}% coverage)`
    if (d.missingSkills.length > 0) details += `. Missing: ${d.missingSkills.slice(0, 5).join(', ')}`
    resultType = d.coveragePercent >= 70 ? 'positive' : d.coveragePercent >= 40 ? 'neutral' : 'negative'
  } else if ('userYears' in detail) {
    const d = detail as ExperienceMatchDetail
    details = `${d.userYears} years of experience${d.requiredYears !== null ? ` (${d.requiredYears} required)` : ''}`
    if (d.titleMatch) details += '. Title match found'
    if (d.leadershipMatch) details += '. Leadership experience detected'
    resultType = d.score >= 0.7 ? 'positive' : d.score >= 0.4 ? 'neutral' : 'negative'
  } else if ('levelMatch' in detail) {
    const d = detail as EducationMatchDetail
    details = `Education level: ${d.userLevel}${d.requiredLevel ? ` (${d.requiredLevel} preferred)` : ''}`
    if (d.fieldMatch && d.requiredField) details += `. Field: ${d.requiredField}`
    resultType = d.score >= 0.7 ? 'positive' : d.score >= 0.4 ? 'neutral' : 'negative'
  } else if ('marketAlignment' in detail) {
    const d = detail as SalaryMatchDetail
    if (d.marketAlignment === 'unknown') {
      details = 'Salary data not available for comparison'
    } else {
      details = `Job salary ${d.marketAlignment === 'within' ? 'aligns with' : d.marketAlignment === 'above' ? 'exceeds' : 'below'} expectations`
    }
    resultType = d.marketAlignment === 'within' ? 'positive' : d.marketAlignment === 'above' ? 'positive' : d.marketAlignment === 'below' ? 'negative' : 'neutral'
  } else if ('remoteMatch' in detail) {
    const d = detail as LocationMatchDetail
    details = d.remoteMatch ? 'Remote work available' : d.locationMatch ? 'Location matches' : d.relocationRequired ? 'Relocation required' : 'Location mismatch'
    resultType = d.score >= 0.7 ? 'positive' : d.score >= 0.4 ? 'neutral' : 'negative'
  } else if ('hasResume' in detail) {
    const d = detail as ResumeMatchDetail
    details = d.hasResume ? `Resume confidence: ${Math.round(d.resumeConfidence * 100)}%` : 'No resume uploaded'
    resultType = d.hasResume ? 'positive' : 'negative'
  }

  return { category, score, weight: Math.round(weight * 100), details, type: resultType }
}
