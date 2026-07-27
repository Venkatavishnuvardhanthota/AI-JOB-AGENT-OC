import type { ExperienceMatchDetail } from './types'
import type { CandidateProfile } from './types'
import type { Job } from '@/services/discovery/types'

export function computeExperienceMatch(job: Job, profile: CandidateProfile): ExperienceMatchDetail {
  const requiredYears = extractRequiredYears(job)
  const userYears = profile.totalYearsOfExperience

  const relevantExperience = profile.experience.some(exp => {
    const titleLower = exp.title.toLowerCase()
    const keywords = job.title.toLowerCase().split(/\s+/)
    return keywords.some(kw => titleLower.includes(kw) || kw.includes(titleLower))
  })

  const titleMatch = profile.experience.some(exp => {
    const jobTitleNorm = job.title.toLowerCase()
    const expTitleNorm = exp.title.toLowerCase()
    if (expTitleNorm.includes(jobTitleNorm) || jobTitleNorm.includes(expTitleNorm)) return true
    const jobWords = new Set(jobTitleNorm.split(/\s+/))
    const expWords = new Set(expTitleNorm.split(/\s+/))
    let matches = 0
    for (const w of jobWords) if (expWords.has(w)) matches++
    return matches >= Math.min(2, jobWords.size)
  })

  const leadershipMatch = profile.experience.some(exp => {
    const t = exp.title.toLowerCase()
    return ['lead', 'senior', 'staff', 'principal', 'head', 'director', 'manager', 'leadership', 'lead engineer', 'tech lead', 'architect', 'vp', 'chief'].some(k => t.includes(k))
  })

  const domainMatch = profile.experience.some(exp => {
    if (!exp.description) return false
    const desc = exp.description.toLowerCase()
    const jobDesc = job.description.toLowerCase()
    const domainWords = extractDomainWords(jobDesc)
    return domainWords.some(word => desc.includes(word))
  })

  let score = 0
  if (requiredYears === null) {
    score = userYears >= 2 ? 0.8 : userYears >= 1 ? 0.5 : 0.3
  } else {
    const ratio = userYears / requiredYears
    if (ratio >= 1.5) score = 1.0
    else if (ratio >= 1.0) score = 0.9
    else if (ratio >= 0.75) score = 0.7
    else if (ratio >= 0.5) score = 0.5
    else score = Math.max(0, ratio * 0.8)
  }

  if (titleMatch) score = Math.min(1, score + 0.1)
  if (relevantExperience && !titleMatch) score = Math.min(1, score + 0.05)
  if (leadershipMatch) score = Math.min(1, score + 0.05)
  if (domainMatch) score = Math.min(1, score + 0.05)

  return {
    userYears,
    requiredYears,
    relevantExperience,
    titleMatch,
    leadershipMatch,
    domainMatch,
    score: Math.round(score * 100) / 100,
  }
}

function extractRequiredYears(job: Job): number | null {
  const text = `${job.title} ${job.description} ${job.experienceLevel || ''}`.toLowerCase()
  const patterns = [
    /(\d+)\+?\s*years?\s*(of\s*)?(experience|exp)/i,
    /(\d+)\s*-\s*(\d+)\s*years?\s*(of\s*)?(experience|exp)/i,
    /(\d+)\s*to\s*(\d+)\s*years?\s*(of\s*)?(experience|exp)/i,
    /experience.*?(\d+).*?years?/i,
  ]
  for (const pattern of patterns) {
    const match = text.match(pattern)
    if (match) {
      if (match[2] && !isNaN(Number(match[2]))) {
        return Math.round((Number(match[1]) + Number(match[2])) / 2)
      }
      return parseInt(match[1], 10)
    }
  }
  if (job.experienceLevel) {
    const levelMap: Record<string, number> = {
      'internship': 0, 'entry': 1, 'associate': 2, 'mid_senior': 5, 'director': 8, 'executive': 10,
    }
    return levelMap[job.experienceLevel] ?? null
  }
  return null
}

const DOMAIN_KEYWORDS = [
  'fintech', 'healthtech', 'edtech', 'ecommerce', 'saas', 'enterprise', 'consumer',
  'mobile', 'cloud', 'security', 'ai', 'ml', 'data', 'analytics', 'devops', 'platform',
  'infrastructure', 'networking', 'gaming', 'social', 'marketplace', 'advertising',
]

function extractDomainWords(text: string): string[] {
  return DOMAIN_KEYWORDS.filter(kw => text.includes(kw))
}
