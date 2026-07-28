import type { ReviewResult, ReviewSeverity, GeneratedResume, GeneratedCoverLetter, QuestionnaireAnswer } from './types'
import { v4Service } from './utils'

const WEAK_WORDS = ['very', 'really', 'quite', 'somewhat', 'maybe', 'stuff', 'things', 'good', 'nice', 'excellent', 'amazing', 'incredible', 'best', 'worst']

const BUZZWORDS = ['synergy', 'leverage', 'paradigm', 'disrupt', 'game-changer', 'bleeding-edge', 'thought-leader', 'circle-back', 'deep-dive', 'move-the-needle', 'low-hanging-fruit', 'bandwidth']

export function reviewPackage(
  resume: GeneratedResume,
  coverLetter: GeneratedCoverLetter | null,
  questionnaire: QuestionnaireAnswer[]
): ReviewResult[] {
  const results: ReviewResult[] = []
  results.push(...reviewResume(resume))
  if (coverLetter) results.push(...reviewCoverLetter(coverLetter))
  results.push(...reviewQuestionnaire(questionnaire))
  results.push(...reviewConsistency(resume, coverLetter, questionnaire))
  return results
}

function reviewResume(resume: GeneratedResume): ReviewResult[] {
  const results: ReviewResult[] = []
  const allText = resume.sections.map(s => s.items.map(i => [i.description, ...i.bullets].join(' ')).join(' ')).join(' ')

  if (resume.metadata.wordCount > 600) {
    results.push(createResult('warning', 'length', 'Resume exceeds 600 words. Consider trimming to fit one page.', 'Reduce bullet points and focus on most relevant achievements.', 'resume'))
  }

  if (resume.metadata.missingKeywords.length > 0) {
    results.push(createResult('warning', 'keywords', `Missing ${resume.metadata.missingKeywords.length} key skills from job description.`, `Add: ${resume.metadata.missingKeywords.slice(0, 5).join(', ')}`, 'resume'))
  }

  const weakWordsFound = WEAK_WORDS.filter(w => allText.toLowerCase().includes(w))
  if (weakWordsFound.length > 0) {
    results.push(createResult('info', 'word_choice', `Weak words detected: ${weakWordsFound.join(', ')}.`, 'Replace with stronger, more specific language.', 'resume'))
  }

  const buzzwordsFound = BUZZWORDS.filter(w => allText.toLowerCase().includes(w))
  if (buzzwordsFound.length > 0) {
    results.push(createResult('warning', 'buzzwords', `Buzzwords detected: ${buzzwordsFound.join(', ')}.`, 'Replace with concrete, specific descriptions of your work.', 'resume'))
  }

  if (resume.sections.filter(s => s.included).length < 3) {
    results.push(createResult('error', 'completeness', 'Resume has fewer than 3 sections.', 'Add more sections for a complete resume.', 'resume'))
  }

  return results
}

function reviewCoverLetter(coverLetter: GeneratedCoverLetter): ReviewResult[] {
  const results: ReviewResult[] = []

  if (coverLetter.metadata.wordCount < 200) {
    results.push(createResult('warning', 'length', 'Cover letter is too short.', 'Add more detail about your qualifications and interest.', 'cover_letter'))
  }

  if (coverLetter.metadata.wordCount > 500) {
    results.push(createResult('warning', 'length', 'Cover letter is too long.', 'Consider condensing to 300-400 words for optimal impact.', 'cover_letter'))
  }

  if (coverLetter.metadata.personalizationScore < 40) {
    results.push(createResult('warning', 'personalization', 'Cover letter lacks personalization.', 'Add specific details about the company and role.', 'cover_letter'))
  }

  return results
}

function reviewQuestionnaire(questionnaire: QuestionnaireAnswer[]): ReviewResult[] {
  const results: ReviewResult[] = []

  const lowConfidence = questionnaire.filter(q => q.confidence < 60)
  if (lowConfidence.length > 0) {
    results.push(createResult('info', 'confidence', `${lowConfidence.length} answers have low confidence.`, 'Review and improve answers for: ' + lowConfidence.map(q => q.topic).join(', '), 'questionnaire'))
  }

  const shortAnswers = questionnaire.filter(q => q.wordCount < 20)
  if (shortAnswers.length > 0) {
    results.push(createResult('warning', 'detail', `${shortAnswers.length} answers are too short.`, 'Provide more detailed responses.', 'questionnaire'))
  }

  return results
}

function reviewConsistency(
  resume: GeneratedResume,
  coverLetter: GeneratedCoverLetter | null,
  questionnaire: QuestionnaireAnswer[]
): ReviewResult[] {
  const results: ReviewResult[] = []

  if (coverLetter) {
    const resumeSkills = new Set(resume.skills.map(s => s.name.toLowerCase()))
    const coverLetterSkills = new Set(coverLetter.metadata.skillMentions.map(s => s.toLowerCase()))

    const extraSkills = [...coverLetterSkills].filter(s => !resumeSkills.has(s))
    if (extraSkills.length > 0) {
      results.push(createResult('info', 'consistency', `Cover letter mentions skills not in resume: ${extraSkills.join(', ')}.`, 'Ensure skills mentioned in cover letter also appear in resume.', 'consistency'))
    }
  }

  const resumeSummary = resume.summary.toLowerCase()
  for (const answer of questionnaire) {
    if (answer.topic === 'about_yourself') {
      const yearMatch = resumeSummary.match(/\d+\+?\s*years?/)
      const answerYearMatch = answer.answer.match(/\d+\+?\s*years?/)
      if (yearMatch && answerYearMatch && yearMatch[0] !== answerYearMatch[0]) {
        results.push(createResult('warning', 'consistency', 'Resume and self-introduction have different stated experience levels.', 'Ensure consistent messaging across all documents.', 'consistency'))
      }
    }
  }

  return results
}

function createResult(severity: ReviewSeverity, category: string, message: string, suggestion: string | null, location: string | null): ReviewResult {
  return { id: v4Service.generate('rev'), severity, category, message, suggestion, location }
}
