export type {
  CandidateProfile, CandidateSkill, CandidateExperience, CandidateEducation,
  CandidateCertification, CandidateLanguage, CandidateProject,
  MatchResult, MatchInput, MatchExplanation,
  SkillMatchDetail, ExperienceMatchDetail, EducationMatchDetail,
  SalaryMatchDetail, LocationMatchDetail, ResumeMatchDetail,
  SkillGapAnalysis, MatchStatistics, MatchHistoryEntry,
  MatchWeights, RankingCriteria, Decision,
} from './types'
export { DEFAULT_MATCH_WEIGHTS } from './types'

export { buildCandidateProfile, createDefaultProfile } from './candidate-profile'
export { matchingService } from './matching'
export { matchHistoryService } from './history'
export { computeSkillMatch } from './skill-matching'
export { computeExperienceMatch } from './experience-matching'
export { computeEducationMatch } from './education-matching'
export { computeSalaryMatch } from './salary-matching'
export { computeLocationMatch } from './location-matching'
export { computeResumeMatch, selectBestResume } from './resume-intelligence'
export { extractJobInfo } from './job-intelligence'
export { makeDecision, getDecisionLabel, getDecisionColor, getDecisionScore } from './decision-engine'
export { generateSkillGapAnalysis } from './gap-analysis'
export { rankJobs, rankByMatch, rankByNewest, rankBySalary, rankByCompany } from './ranking'
export { normalizeSkill, expandSkill, areSkillsSimilar, findMatchingSkills } from './skill-synonyms'
