import type { Job } from '@/services/discovery/types'

export type Decision = 'apply_immediately' | 'high_priority' | 'good_match' | 'consider' | 'low_match' | 'skip'

export interface CandidateProfile {
  preferredRoles: string[]
  headline: string | null
  bio: string | null
  location: string | null
  salaryExpectationMin: number | null
  salaryExpectationMax: number | null
  salaryCurrency: string | null
  portfolioUrl: string | null
  linkedinUrl: string | null
  githubUrl: string | null
  skills: CandidateSkill[]
  experience: CandidateExperience[]
  education: CandidateEducation[]
  certifications: CandidateCertification[]
  languages: CandidateLanguage[]
  projects: CandidateProject[]
  visaSponsorshipRequired: boolean
  remotePreference: string | null
  preferredLocations: string[]
  employmentType: string | null
  totalYearsOfExperience: number
}

export interface CandidateSkill {
  name: string
  category: string | null
  proficiency: number | null
}

export interface CandidateExperience {
  title: string
  company: string
  location: string | null
  startDate: string | null
  endDate: string | null
  isCurrent: boolean
  description: string | null
}

export interface CandidateEducation {
  institution: string
  degree: string
  fieldOfStudy: string | null
  startDate: string | null
  endDate: string | null
  gpa: number | null
}

export interface CandidateCertification {
  name: string
  issuer: string | null
}

export interface CandidateLanguage {
  name: string
  proficiency: string
}

export interface CandidateProject {
  name: string
  description: string | null
  url: string | null
}

export interface MatchInput {
  job: Job
  profile: CandidateProfile
  resumeId: string | null
}

export interface MatchResult {
  jobId: string
  job: Job
  overall: number
  confidence: number
  decision: Decision
  skillScore: number
  skillDetail: SkillMatchDetail
  experienceScore: number
  experienceDetail: ExperienceMatchDetail
  educationScore: number
  educationDetail: EducationMatchDetail
  salaryScore: number
  salaryDetail: SalaryMatchDetail
  locationScore: number
  locationDetail: LocationMatchDetail
  resumeScore: number
  resumeDetail: ResumeMatchDetail
  explanations: MatchExplanation[]
  missingSkills: string[]
  recommendedLearning: string[]
  recommendedResumeId: string | null
  scoredAt: string
}

export interface SkillMatchDetail {
  exactMatches: string[]
  similarMatches: string[]
  missingSkills: string[]
  transferableSkills: string[]
  totalJobSkills: number
  matchedCount: number
  coveragePercent: number
}

export interface ExperienceMatchDetail {
  userYears: number
  requiredYears: number | null
  relevantExperience: boolean
  titleMatch: boolean
  leadershipMatch: boolean
  domainMatch: boolean
  score: number
}

export interface EducationMatchDetail {
  levelMatch: boolean
  fieldMatch: boolean
  userLevel: string
  requiredLevel: string | null
  userField: string | null
  requiredField: string | null
  score: number
}

export interface SalaryMatchDetail {
  jobMin: number | null
  jobMax: number | null
  userMin: number | null
  userMax: number | null
  currency: string | null
  marketAlignment: 'below' | 'within' | 'above' | 'unknown'
  score: number
}

export interface LocationMatchDetail {
  remoteMatch: boolean
  locationMatch: boolean
  relocationRequired: boolean
  remotePreference: string | null
  jobRemote: string
  score: number
}

export interface ResumeMatchDetail {
  hasResume: boolean
  resumeConfidence: number
  score: number
}

export interface MatchExplanation {
  category: string
  score: number
  weight: number
  details: string
  type: 'positive' | 'negative' | 'neutral'
}

export interface SkillGapAnalysis {
  missingSkills: string[]
  recommendedLearning: { skill: string; priority: 'high' | 'medium' | 'low'; reason: string }[]
  quickWins: string[]
  longTermImprovements: string[]
  coveragePercent: number
}

export interface RankingCriteria {
  field: 'match' | 'date' | 'salary' | 'experience' | 'company'
  direction: 'desc' | 'asc'
}

export interface MatchStatistics {
  totalScored: number
  averageScore: number
  averageConfidence: number
  decisionBreakdown: Record<Decision, number>
  averageSkillScore: number
  averageExperienceScore: number
  averageSalaryScore: number
  averageLocationScore: number
  topSkills: { skill: string; count: number }[]
  commonMissingSkills: { skill: string; count: number }[]
}

export interface MatchHistoryEntry {
  id: string
  jobId: string
  jobTitle: string
  company: string
  overall: number
  decision: Decision
  resumeId: string | null
  scoredAt: string
}

export interface MatchWeights {
  skill: number
  experience: number
  education: number
  salary: number
  location: number
  resume: number
  projects: number
  certifications: number
}

export const DEFAULT_MATCH_WEIGHTS: MatchWeights = {
  skill: 0.35,
  experience: 0.20,
  education: 0.10,
  salary: 0.10,
  location: 0.10,
  resume: 0.05,
  projects: 0.05,
  certifications: 0.05,
}
