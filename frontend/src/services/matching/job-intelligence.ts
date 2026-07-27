import type { Job } from '@/services/discovery/types'

export interface ExtractedJobInfo {
  title: string
  company: string
  requiredSkills: string[]
  preferredSkills: string[]
  experienceRequired: string | null
  seniority: string | null
  technologies: string[]
  responsibilities: string[]
  educationRequirements: string[]
  certifications: string[]
  salaryRange: { min: number | null; max: number | null; currency: string | null }
  remoteEligible: boolean
  employmentType: string
}

export function extractJobInfo(job: Job): ExtractedJobInfo {
  const description = job.description || ''
  const lower = description.toLowerCase()

  return {
    title: job.title,
    company: job.company,
    requiredSkills: job.requiredSkills || [],
    preferredSkills: job.preferredSkills || [],
    experienceRequired: extractExperienceRequirement(lower),
    seniority: job.experienceLevel || extractSeniority(job.title, lower),
    technologies: extractTechnologies([...job.requiredSkills, ...job.preferredSkills, ...extractTechKeywords(lower)]),
    responsibilities: job.responsibilities?.length > 0 ? job.responsibilities : extractResponsibilities(description),
    educationRequirements: extractEducation(lower),
    certifications: extractCertifications(lower),
    salaryRange: { min: job.salaryMin, max: job.salaryMax, currency: job.currency },
    remoteEligible: job.remote === 'remote' || job.remote === 'hybrid',
    employmentType: job.employmentType || 'full_time',
  }
}

function extractExperienceRequirement(text: string): string | null {
  const patterns = [
    /(\d+)\+?\s*years?\s*(of\s*)?(experience|exp)/i,
    /(\d+)\s*-\s*(\d+)\s*years?\s*(of\s*)?(experience|exp)/i,
    /experience.*?(\d+)\+?\s*years?/i,
  ]
  for (const pattern of patterns) {
    const match = text.match(pattern)
    if (match) return match[0].trim()
  }
  return null
}

function extractSeniority(title: string, description: string): string | null {
  const text = `${title} ${description}`.toLowerCase()
  if (/\b(chief|ceo|cto|vp\b|vice president)\b/.test(text)) return 'executive'
  if (/\b(director|head of)\b/.test(text)) return 'director'
  if (/\b(staff|principal|distinguished)\b/.test(text)) return 'staff'
  if (/\b(senior|sr\.?|lead)\b/.test(text)) return 'senior'
  if (/\b(mid|intermediate)\b/.test(text)) return 'mid'
  if (/\b(junior|jr\.?|entry|graduate|fresher)\b/.test(text)) return 'junior'
  if (/\bintern(ship)?\b/.test(text)) return 'internship'
  return null
}

const TECH_KEYWORDS = [
  'react', 'angular', 'vue', 'node', 'typescript', 'javascript', 'python', 'java', 'go', 'rust',
  'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'terraform', 'jenkins', 'graphql', 'rest',
  'postgresql', 'mongodb', 'redis', 'kafka', 'rabbitmq', 'elasticsearch', 'nginx',
  'ci/cd', 'machine learning', 'deep learning', 'nlp', 'computer vision',
  'react native', 'flutter', 'swift', 'kotlin', 'dart',
  'spring', 'django', 'flask', 'rails', 'laravel', 'express',
  'webpack', 'vite', 'next.js', 'nuxt', 'tailwind', 'sass',
]

function extractTechKeywords(text: string): string[] {
  return TECH_KEYWORDS.filter(kw => text.includes(kw.toLowerCase()))
}

function extractTechnologies(skills: string[]): string[] {
  return [...new Set(skills.map(s => s.toLowerCase()))]
}

function extractResponsibilities(text: string): string[] {
  const lines = text.split(/[.\n]/).map(l => l.trim()).filter(l => l.length > 10)
  const responsibilityMarkers = ['responsible for', 'duties include', 'will', 'lead', 'manage', 'develop', 'design', 'implement', 'maintain', 'build', 'create', 'drive', 'own', 'deliver', 'collaborate']
  return lines.filter(line => responsibilityMarkers.some(m => line.toLowerCase().includes(m))).slice(0, 10)
}

function extractEducation(text: string): string[] {
  const requirements: string[] = []
  const patterns = [
    /bachelor['’]?s?\s*(degree)?\s*(in|of)?\s*(\w+\s*\w*)/i,
    /master['’]?s?\s*(degree)?\s*(in|of)?\s*(\w+\s*\w*)/i,
    /ph\.?d/i,
    /mba/i,
    /associate['’]?s?\s*(degree)?/i,
  ]
  for (const pattern of patterns) {
    const match = text.match(pattern)
    if (match) requirements.push(match[0].trim())
  }
  return [...new Set(requirements)]
}

function extractCertifications(text: string): string[] {
  const certs: string[] = []
  const patterns = [
    /(AWS\s*Certified\s*\w+)/i,
    /(Google\s*Cloud\s*Certified)/i,
    /(Microsoft\s*Certified)/i,
    /(CISSP|CISM|PMP|SCJP|OCJP|CEH|CCNA|CCNP|CFA|CPA|FRM)/i,
    /certified\s+(\w+\s*\w*)/i,
  ]
  for (const pattern of patterns) {
    const matches = text.matchAll(pattern)
    for (const match of matches) {
      certs.push(match[0].trim())
    }
  }
  return [...new Set(certs)]
}
