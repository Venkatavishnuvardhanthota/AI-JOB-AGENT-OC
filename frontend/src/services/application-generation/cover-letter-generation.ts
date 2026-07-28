import type { GeneratedCoverLetter, CoverLetterMetadata, GenerationRequest } from './types'
import { v4Service } from './utils'

export function generateCoverLetter(
  request: GenerationRequest,
  projects: { name: string; technologies: string[]; description: string; relevance: number }[],
  summary: string
): GeneratedCoverLetter {
  const id = v4Service.generate('clGen')
  const relevantProjects = projects.filter(p => p.relevance > 0.3).slice(0, 2)
  const skillMentions = request.requiredSkills.slice(0, 5)
  const projectMentions = relevantProjects.map(p => p.name)

  const body = buildCoverLetterBody(request, relevantProjects, summary)
  const wordCount = body.split(/\s+/).length

  const metadata: CoverLetterMetadata = {
    tone: 'professional',
    wordCount,
    targetLength: 350,
    personalizationScore: calculatePersonalization(request),
    companyMentions: body.split(request.companyName).length - 1,
    skillMentions,
    projectMentions,
  }

  return {
    id,
    versionId: v4Service.generate('ver'),
    jobId: request.jobId,
    companyName: request.companyName,
    hiringManagerName: null,
    subject: `Application for ${request.jobTitle} at ${request.companyName}`,
    body,
    closing: buildCoverLetterClosing(request),
    metadata,
    createdAt: new Date().toISOString(),
  }
}

function buildCoverLetterBody(
  request: GenerationRequest,
  projects: { name: string; technologies: string[]; description: string }[],
  summary: string
): string {
  const paragraphs: string[] = []

  paragraphs.push(`Dear Hiring Manager,`)
  paragraphs.push(`I am writing to express my strong interest in the ${request.jobTitle} position at ${request.companyName}. ${summary}`)

  const relevantSkills = request.requiredSkills.slice(0, 4)
  if (relevantSkills.length > 0) {
    paragraphs.push(`My technical expertise spans ${relevantSkills.join(', ')}, which aligns closely with the requirements for this role.${request.companyIndustry ? ` I have a deep understanding of the ${request.companyIndustry} domain and its unique challenges.` : ''}`)
  }

  if (projects.length > 0) {
    const projectDetails = projects.map(p => `${p.name} (${p.technologies.slice(0, 3).join(', ')})`).join(' and ')
    paragraphs.push(`In my recent work on ${projectDetails}, I have demonstrated the ability to deliver high-quality solutions that drive business value. These experiences have prepared me to contribute effectively to the ${request.jobTitle} role.`)
  }

  if (request.responsibilities.length > 0) {
    const responsibilities = request.responsibilities.slice(0, 3).map(r => r.toLowerCase()).join(', ')
    paragraphs.push(`I am particularly drawn to this opportunity because of the focus on ${responsibilities}, areas where I have proven expertise and a genuine passion.`)
  }

  paragraphs.push(`I am excited about the opportunity to bring my unique combination of skills and experience to ${request.companyName} and would welcome the chance to discuss how I can contribute to your team's success.`)

  return paragraphs.join('\n\n')
}

function buildCoverLetterClosing(request: GenerationRequest): string {
  return `Best regards,\n[Your Name]\n${request.requiredSkills.slice(0, 3).join(', ')} | ${request.jobTitle}`
}

function calculatePersonalization(request: GenerationRequest): number {
  let score = 0
  if (request.companyName) score += 20
  if (request.companyDescription) score += 15
  if (request.companyIndustry) score += 15
  if (request.responsibilities.length > 0) score += 20
  if (request.requiredSkills.length > 0) score += 15
  if (request.preferredSkills.length > 0) score += 10
  if (request.jobDescription.length > 100) score += 5
  return Math.min(score, 100)
}
