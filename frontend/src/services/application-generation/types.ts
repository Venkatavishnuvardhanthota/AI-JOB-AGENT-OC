export type GenerationStatus = 'draft' | 'ready' | 'needs_review' | 'exported' | 'archived'
export type ExportFormat = 'pdf' | 'docx' | 'markdown' | 'json' | 'bundle'
export type ReviewSeverity = 'error' | 'warning' | 'info'
export type QuestionnaireTopic =
  | 'about_yourself' | 'why_company' | 'why_role' | 'expected_salary'
  | 'notice_period' | 'work_authorization' | 'availability' | 'leadership'
  | 'conflict_resolution' | 'strengths' | 'weaknesses' | 'career_goals'
  | 'behavioral' | 'technical' | 'teamwork' | 'achievements'
export type SectionReorderMode = 'ats_first' | 'highlight_strengths' | 'chronological' | 'custom'

export interface GenerationRequest {
  jobId: string
  jobTitle: string
  companyName: string
  companyIndustry: string
  companyDescription: string
  jobDescription: string
  requiredSkills: string[]
  preferredSkills: string[]
  experienceLevel: string
  educationRequired: string
  certificationsRequired: string[]
  responsibilities: string[]
  salaryRange: { min: number; max: number; currency: string } | null
  remote: boolean
  location: string
  applicationUrl: string | null
}

export interface GeneratedResume {
  id: string
  versionId: string
  jobId: string
  summary: string
  sections: ResumeSection[]
  skills: PrioritizedSkill[]
  ordering: SectionOrder[]
  metadata: ResumeMetadata
  createdAt: string
}

export interface ResumeSection {
  id: string
  type: 'contact' | 'summary' | 'experience' | 'education' | 'skills' | 'projects' | 'certifications' | 'achievements' | 'publications' | 'languages'
  title: string
  items: ResumeSectionItem[]
  relevance: number
  included: boolean
}

export interface ResumeSectionItem {
  id: string
  title: string
  subtitle: string
  dateRange: string | null
  description: string
  bullets: string[]
  relevance: number
  skills: string[]
}

export interface SectionOrder {
  sectionId: string
  position: number
}

export interface PrioritizedSkill {
  name: string
  category: string
  proficiency: number
  matchScore: number
  priority: number
  highlighted: boolean
}

export interface ResumeMetadata {
  sourceResumeId: string | null
  selectionReason: string
  optimized: boolean
  atsScore: number
  missingKeywords: string[]
  improvements: string[]
  wordCount: number
  targetLength: number
}

export interface GeneratedCoverLetter {
  id: string
  versionId: string
  jobId: string
  companyName: string
  hiringManagerName: string | null
  subject: string
  body: string
  closing: string
  metadata: CoverLetterMetadata
  createdAt: string
}

export interface CoverLetterMetadata {
  tone: 'professional' | 'enthusiastic' | 'confident' | 'warm'
  wordCount: number
  targetLength: number
  personalizationScore: number
  companyMentions: number
  skillMentions: string[]
  projectMentions: string[]
}

export interface QuestionnaireAnswer {
  topic: QuestionnaireTopic
  question: string
  answer: string
  wordCount: number
  confidence: number
}

export interface PortfolioSelection {
  portfolioUrl: string | null
  githubRepos: { name: string; url: string; relevance: number; description: string }[]
  liveDemos: { name: string; url: string; relevance: number }[]
  caseStudies: { title: string; url: string; relevance: number; summary: string }[]
  blogs: { title: string; url: string; relevance: number }[]
}

export interface ApplicationPackage {
  id: string
  versionId: string
  jobId: string
  jobTitle: string
  companyName: string
  resume: GeneratedResume
  coverLetter: GeneratedCoverLetter | null
  questionnaire: QuestionnaireAnswer[]
  portfolio: PortfolioSelection
  certificates: CertificateSelection[]
  metadata: PackageMetadata
  status: GenerationStatus
  createdAt: string
  updatedAt: string
}

export interface CertificateSelection {
  name: string
  issuer: string
  date: string | null
  relevance: number
  included: boolean
}

export interface PackageMetadata {
  confidenceScore: number
  qualityScores: QualityScores
  reviewResults: ReviewResult[]
  generationTime: number
  version: number
  exported: boolean
  exportFormats: ExportFormat[]
}

export interface QualityScores {
  resume: number
  coverLetter: number | null
  questionnaire: number
  package: number
  atsReadiness: number
  professionalTone: number
  completeness: number
}

export interface ReviewResult {
  id: string
  severity: ReviewSeverity
  category: string
  message: string
  suggestion: string | null
  location: string | null
}

export interface VersionEntry {
  id: string
  packageId: string
  version: number
  status: GenerationStatus
  confidenceScore: number
  createdAt: string
  parentVersionId: string | null
  changes: string[]
}

export interface ExportResult {
  packageId: string
  format: ExportFormat
  url: string
  filename: string
  size: number
  createdAt: string
}

export interface ProjectRanking {
  name: string
  description: string
  technologies: string[]
  relevance: number
  impact: number
  recency: number
  domainMatch: number
  overallScore: number
  included: boolean
  exclusionReason: string | null
}

export interface GenerationStatistics {
  totalPackages: number
  readyToApply: number
  needsReview: number
  averageConfidence: number
  averageResumeScore: number
  averageCoverLetterScore: number
  averagePackageScore: number
  recentPackages: ApplicationPackage[]
  generationTrend: { date: string; count: number }[]
}
