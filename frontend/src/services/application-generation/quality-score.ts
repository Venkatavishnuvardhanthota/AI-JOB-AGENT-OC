import type { QualityScores, GeneratedResume, GeneratedCoverLetter, QuestionnaireAnswer } from './types'
import { calculateATSScore } from './resume-generation'

export function computeQualityScores(
  resume: GeneratedResume | null,
  coverLetter: GeneratedCoverLetter | null,
  questionnaire: QuestionnaireAnswer[]
): QualityScores {
  const raw: QualityScores = {
    resume: resume ? computeResumeQuality(resume) : 0,
    coverLetter: coverLetter ? computeCoverLetterQuality(coverLetter) : null,
    questionnaire: computeQuestionnaireQuality(questionnaire),
    package: 0,
    atsReadiness: resume ? computeATSReadiness(resume) : 0,
    professionalTone: computeProfessionalTone(resume, coverLetter, questionnaire),
    completeness: computeCompleteness(resume, coverLetter, questionnaire),
  }
  raw.package = computeOverallPackageScore(raw)
  return raw
}

export function computeOverallPackageScore(scores: QualityScores): number {
  const resumeWeight = 0.35
  const coverLetterWeight = scores.coverLetter !== null ? 0.20 : 0
  const questionnaireWeight = 0.15
  const atsWeight = 0.15
  const toneWeight = 0.10
  const completenessWeight = 0.05

  const totalWeight = resumeWeight + coverLetterWeight + questionnaireWeight + atsWeight + toneWeight + completenessWeight
  const weighted = resumeWeight * scores.resume
    + (coverLetterWeight > 0 ? coverLetterWeight * (scores.coverLetter ?? 0) : 0)
    + questionnaireWeight * scores.questionnaire
    + atsWeight * scores.atsReadiness
    + toneWeight * scores.professionalTone
    + completenessWeight * scores.completeness

  return totalWeight > 0 ? Math.round(weighted / totalWeight) : 0
}

function computeResumeQuality(resume: GeneratedResume): number {
  let score = 0
  const included = resume.sections.filter(s => s.included)
  score += (included.length / Math.max(resume.sections.length, 1)) * 20
  score += Math.min(resume.metadata.wordCount / 400, 1) * 15
  score += Math.min(resume.skills.filter(s => s.highlighted).length, 10) * 3
  score += (resume.metadata.atsScore / 100) * 30
  score += resume.metadata.missingKeywords.length === 0 ? 10 : Math.max(0, 10 - resume.metadata.missingKeywords.length * 2)
  score += included.some(s => s.items.some(i => i.bullets.length > 1)) ? 10 : 0
  return Math.round(Math.min(score, 100))
}

function computeCoverLetterQuality(coverLetter: GeneratedCoverLetter): number {
  let score = 0
  score += Math.min(coverLetter.metadata.wordCount / 350, 1) * 30
  score += (coverLetter.metadata.personalizationScore / 100) * 30
  score += Math.min(coverLetter.metadata.skillMentions.length, 5) * 5
  score += Math.min(coverLetter.metadata.projectMentions.length, 2) * 5
  score += coverLetter.metadata.companyMentions > 0 ? 10 : 0
  score += coverLetter.metadata.tone === 'professional' ? 10 : 5
  return Math.round(Math.min(score, 100))
}

function computeQuestionnaireQuality(questionnaire: QuestionnaireAnswer[]): number {
  if (questionnaire.length === 0) return 0
  const avgConfidence = questionnaire.reduce((s, q) => s + q.confidence, 0) / questionnaire.length
  const avgWordCount = questionnaire.reduce((s, q) => s + Math.min(q.wordCount / 30, 1), 0) / questionnaire.length
  return Math.round(avgConfidence * 0.6 + avgWordCount * 40)
}

function computeATSReadiness(resume: GeneratedResume): number {
  return calculateATSScore(resume.skills, resume.metadata.missingKeywords, resume.sections)
}

function computeProfessionalTone(
  resume: GeneratedResume | null,
  coverLetter: GeneratedCoverLetter | null,
  questionnaire: QuestionnaireAnswer[]
): number {
  let score = 70
  if (resume) {
    score += resume.metadata.missingKeywords.length === 0 ? 10 : 0
    score += resume.sections.filter(s => s.included).length >= 4 ? 10 : 0
  }
  if (coverLetter) {
    score += coverLetter.metadata.tone === 'professional' ? 10 : 5
  }
  if (questionnaire.length >= 8) score += 5
  return Math.min(score, 100)
}

function computeCompleteness(
  resume: GeneratedResume | null,
  coverLetter: GeneratedCoverLetter | null,
  questionnaire: QuestionnaireAnswer[]
): number {
  let score = 0
  if (resume) {
    score += 25
    score += Math.min(resume.sections.filter(s => s.included).length * 5, 25)
  }
  if (coverLetter) score += 20
  score += Math.min(questionnaire.length * 3, 20)
  score += 10
  return Math.min(score, 100)
}
