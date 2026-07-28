import type { ApplicationPackage, PackageMetadata, PortfolioSelection, CertificateSelection, GenerationRequest, GeneratedResume, GeneratedCoverLetter, QuestionnaireAnswer, QualityScores, ReviewResult } from './types'
import { v4Service } from './utils'
import { generateResume } from './resume-generation'
import { generateCoverLetter } from './cover-letter-generation'
import { generateAllDefaultAnswers } from './questionnaire-engine'
import { computeQualityScores } from './quality-score'
import { reviewPackage } from './review-engine'

export function buildPackage(
  request: GenerationRequest,
  options: {
    includeCoverLetter?: boolean
    questionnaireTopics?: string[]
    projects?: { name: string; technologies: string[]; description: string; relevance: number }[]
    portfolioUrls?: PortfolioSelection
  } = {}
): ApplicationPackage {
  const id = v4Service.generate('pkg')
  const projects = options.projects || []
  const portfolio = options.portfolioUrls || selectPortfolio(request, projects)
  const certificates = selectCertificates(request)

  const resume = generateResume(request, projects.map(p => ({
    name: p.name, description: p.description, technologies: p.technologies,
    relevance: p.relevance, impact: 0.5, recency: 0.5, domainMatch: p.relevance,
    overallScore: p.relevance, included: p.relevance > 0.3, exclusionReason: null,
  })))

  const coverLetter = options.includeCoverLetter !== false
    ? generateCoverLetter(request, projects, resume.summary)
    : null

  const questionnaire = generateAllDefaultAnswers(request)

  return finalizePackage(id, request, resume, coverLetter, questionnaire, portfolio, certificates)
}

export function rebuildPackage(
  existing: ApplicationPackage,
  request: GenerationRequest
): ApplicationPackage {
  const resume = generateResume(request, [])
  const coverLetter = existing.coverLetter
    ? generateCoverLetter(request, [], resume.summary)
    : null
  const questionnaire = generateAllDefaultAnswers(request)

  return finalizePackage(
    existing.id,
    request,
    resume,
    coverLetter,
    questionnaire,
    existing.portfolio,
    existing.certificates
  )
}

function finalizePackage(
  id: string,
  request: GenerationRequest,
  resume: GeneratedResume,
  coverLetter: GeneratedCoverLetter | null,
  questionnaire: QuestionnaireAnswer[],
  portfolio: PortfolioSelection,
  certificates: CertificateSelection[]
): ApplicationPackage {
  const startTime = Date.now()
  const qualityScores = computeQualityScores(resume, coverLetter, questionnaire)
  const reviewResults = reviewPackage(resume, coverLetter, questionnaire)
  const confidenceScore = calculateConfidenceScore(qualityScores, reviewResults)

  const metadata: PackageMetadata = {
    confidenceScore,
    qualityScores,
    reviewResults,
    generationTime: Date.now() - startTime,
    version: 1,
    exported: false,
    exportFormats: [],
  }

  return {
    id,
    versionId: v4Service.generate('ver'),
    jobId: request.jobId,
    jobTitle: request.jobTitle,
    companyName: request.companyName,
    resume,
    coverLetter,
    questionnaire,
    portfolio,
    certificates,
    metadata,
    status: metadata.confidenceScore >= 70 ? 'ready' : 'needs_review',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }
}

function calculateConfidenceScore(scores: QualityScores, reviews: ReviewResult[]): number {
  const errorCount = reviews.filter(r => r.severity === 'error').length
  const warningCount = reviews.filter(r => r.severity === 'warning').length
  const baseScore = scores.package
  const penalty = errorCount * 10 + warningCount * 3
  return Math.max(0, Math.min(100, baseScore - penalty))
}

export function selectPortfolio(
  _request: GenerationRequest,
  projects: { name: string; technologies: string[]; relevance: number; description?: string }[]
): PortfolioSelection {
  const relevantGithub = projects
    .filter(p => p.relevance > 0.3)
    .slice(0, 3)
    .map(p => ({
      name: p.name,
      url: `https://github.com/user/${p.name.replace(/\s+/g, '-').toLowerCase()}`,
      relevance: p.relevance,
      description: p.description || 'Project',
    }))

  return {
    portfolioUrl: null,
    githubRepos: relevantGithub,
    liveDemos: [],
    caseStudies: [],
    blogs: [],
  }
}

export function selectCertificates(request: GenerationRequest): CertificateSelection[] {
  return request.certificationsRequired.map(c => ({
    name: c,
    issuer: '',
    date: null,
    relevance: 1,
    included: true,
  }))
}
