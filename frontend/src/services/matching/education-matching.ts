import type { EducationMatchDetail } from './types'
import type { CandidateProfile } from './types'
import type { Job } from '@/services/discovery/types'

const DEGREE_ORDER: Record<string, number> = {
  'high school': 0,
  'diploma': 1,
  'associate': 2,
  "associate's": 2,
  'associates': 2,
  'bachelor': 3,
  "bachelor's": 3,
  'bachelors': 3,
  'b.tech': 3,
  'b.e.': 3,
  'be': 3,
  'b.sc': 3,
  'b.s.': 3,
  'master': 4,
  "master's": 4,
  'masters': 4,
  'm.tech': 4,
  'm.e.': 4,
  'm.sc': 4,
  'm.s.': 4,
  'mba': 4,
  'doctorate': 5,
  'phd': 5,
  'ph.d': 5,
}

const FIELD_SYNONYMS: Record<string, string[]> = {
  'computer science': ['cs', 'computer science', 'computerscience', 'computing', 'computer engineering'],
  'software engineering': ['software engineering', 'software engineer', 'software development', 'software dev'],
  'information technology': ['it', 'information technology', 'information systems', 'information tech'],
  'data science': ['data science', 'datascience', 'data analytics', 'analytics'],
  'electrical engineering': ['ee', 'electrical engineering', 'electrical', 'electronics'],
  'mechanical engineering': ['mechanical engineering', 'mechanical'],
  'mathematics': ['math', 'mathematics', 'applied mathematics', 'statistics'],
  'business': ['business administration', 'business management', 'busienss', 'business'],
  'physics': ['physics', 'applied physics'],
  'biology': ['biology', 'biological sciences', 'biotechnology'],
}

export function computeEducationMatch(job: Job, profile: CandidateProfile): EducationMatchDetail {
  const requiredLevel = extractRequiredEducation(job)
  const requiredField = extractRequiredField(job)

  const highestLevel = profile.education.length > 0
    ? findHighestDegree(profile.education.map(e => e.degree))
    : null

  const userFields = profile.education.map(e => e.fieldOfStudy).filter(Boolean) as string[]
  const userField = userFields.length > 0 ? findMostRelevantField(userFields, requiredField) : null

  const levelMatch = compareDegrees(highestLevel, requiredLevel)
  const fieldMatch = requiredField ? userFields.some(f => fieldsMatch(f, requiredField!)) : true

  let score = 0
  if (requiredLevel === null) {
    score = highestLevel ? 0.8 : 0.3
  } else if (!highestLevel) {
    score = 0.2
  } else if (levelMatch) {
    score = 0.9
    if (fieldMatch) score = 1.0
  } else {
    const userOrd = DEGREE_ORDER[highestLevel.toLowerCase()] ?? -1
    const reqOrd = DEGREE_ORDER[requiredLevel.toLowerCase()] ?? 0
    if (userOrd >= reqOrd) score = 0.7
    else score = Math.max(0.2, userOrd / Math.max(reqOrd, 1))
  }

  return {
    levelMatch,
    fieldMatch: requiredField ? fieldMatch : true,
    userLevel: highestLevel || 'none',
    requiredLevel,
    userField,
    requiredField,
    score: Math.round(score * 100) / 100,
  }
}

function extractRequiredEducation(job: Job): string | null {
  const lower = `${job.title} ${job.description}`.toLowerCase()
  const degreePatterns = [
    { pattern: /ph\.?d/i, degree: 'phd' },
    { pattern: /master['’]?s|m\.?tech|m\.?s\.?/i, degree: "master's" },
    { pattern: /doctorate/i, degree: 'phd' },
    { pattern: /bachelor['’]?s|b\.?tech|b\.?e\.?|b\.?s\.?/i, degree: "bachelor's" },
    { pattern: /associate['’]?s/i, degree: "associate's" },
    { pattern: /diploma/i, degree: 'diploma' },
  ]
  for (const { pattern, degree } of degreePatterns) {
    if (pattern.test(lower)) return degree
  }
  if (/mba/i.test(lower)) return "master's"
  return null
}

function extractRequiredField(job: Job): string | null {
  const lower = `${job.title} ${job.description}`.toLowerCase()
  const fields = Object.keys(FIELD_SYNONYMS)
  for (const field of fields) {
    const synonyms = FIELD_SYNONYMS[field]
    if (synonyms.some(s => lower.includes(s))) return field
  }
  return null
}

function findHighestDegree(degrees: string[]): string | null {
  let highest: string | null = null
  let highestOrd = -1
  for (const degree of degrees) {
    const ord = DEGREE_ORDER[degree.toLowerCase().trim()] ?? -1
    if (ord > highestOrd) {
      highestOrd = ord
      highest = degree
    }
  }
  return highest
}

function findMostRelevantField(fields: string[], targetField: string | null): string | null {
  if (!targetField) return fields[0] ?? null
  for (const field of fields) {
    if (fieldsMatch(field, targetField)) return field
  }
  return fields[0] ?? null
}

function fieldsMatch(userField: string, requiredField: string): boolean {
  const u = userField.toLowerCase().trim()
  const r = requiredField.toLowerCase().trim()
  if (u === r) return true
  const synonyms = FIELD_SYNONYMS[r]
  if (synonyms && synonyms.some(s => u.includes(s) || s.includes(u))) return true
  for (const [, aliases] of Object.entries(FIELD_SYNONYMS)) {
    if (aliases.includes(u) && aliases.includes(r)) return true
  }
  return false
}

function compareDegrees(user: string | null, required: string | null): boolean {
  if (!user || !required) return false
  const uOrd = DEGREE_ORDER[user.toLowerCase().trim()] ?? -1
  const rOrd = DEGREE_ORDER[required.toLowerCase().trim()] ?? 0
  return uOrd >= rOrd
}
