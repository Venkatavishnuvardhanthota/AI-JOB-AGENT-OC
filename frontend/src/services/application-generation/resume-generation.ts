import type { GeneratedResume, ResumeSection, ResumeSectionItem, SectionOrder, PrioritizedSkill, ResumeMetadata, GenerationRequest, ProjectRanking } from './types'
import { v4Service } from './utils'

const ATS_KEYWORDS = ['achieved', 'implemented', 'developed', 'led', 'managed', 'created', 'designed', 'delivered', 'improved', 'reduced', 'increased', 'optimized', 'drove', 'established', 'launched', 'spearheaded', 'transformed', 'architected', 'engineered', 'orchestrated']

const ACTION_VERBS = ['achieve', 'implement', 'develop', 'lead', 'manage', 'create', 'design', 'deliver', 'improve', 'reduce', 'increase', 'optimize', 'drive', 'establish', 'launch', 'build', 'architect', 'engineer', 'integrate', 'migrate', 'deploy', 'automate', 'configure', 'refactor']

export function generateResume(request: GenerationRequest, projects: ProjectRanking[]): GeneratedResume {
  const id = v4Service.generate('resumeGen')
  const skills = prioritizeSkills(request.requiredSkills, request.preferredSkills)
  const sections = buildSections(request, projects, skills)
  const ordering = determineOrdering(sections, request)
  const wordCount = sections.reduce((sum, s) => sum + s.items.reduce((si, i) => si + i.bullets.join(' ').length, 0), 0)

  const missingKeywords = findMissingKeywords(request.requiredSkills, skills)
  const improvements = generateImprovements(missingKeywords, wordCount)

  const metadata: ResumeMetadata = {
    sourceResumeId: null,
    selectionReason: 'Generated from candidate profile and job requirements',
    optimized: true,
    atsScore: calculateATSScore(skills, missingKeywords, sections),
    missingKeywords,
    improvements,
    wordCount: Math.round(wordCount / 5),
    targetLength: 500,
  }

  return { id, versionId: v4Service.generate('ver'), jobId: request.jobId, summary: generateSummary(request, skills), sections, skills, ordering, metadata, createdAt: new Date().toISOString() }
}

function prioritizeSkills(required: string[], preferred: string[]): PrioritizedSkill[] {
  const all = new Map<string, { category: string; proficiency: number }>()
  const categories: Record<string, string> = {
    typescript: 'language', javascript: 'language', python: 'language', go: 'language', java: 'language', rust: 'language',
    react: 'frontend', angular: 'frontend', vue: 'frontend', css: 'frontend', html: 'frontend',
    node: 'backend', express: 'backend', django: 'backend', flask: 'backend', spring: 'backend',
    aws: 'cloud', azure: 'cloud', gcp: 'cloud', docker: 'devops', kubernetes: 'devops', terraform: 'devops',
    postgresql: 'database', mongodb: 'database', redis: 'database', mysql: 'database', sql: 'database',
    graphql: 'api', rest: 'api', grpc: 'api',
  }

  required.forEach((s, i) => {
    const lower = s.toLowerCase()
    all.set(lower, { category: categories[lower] || 'other', proficiency: Math.max(5 - Math.floor(i / 3), 3) })
  })
  preferred.forEach(s => {
    const lower = s.toLowerCase()
    if (!all.has(lower)) all.set(lower, { category: categories[lower] || 'other', proficiency: 3 })
  })

  return Array.from(all.entries()).map(([name, info], i) => ({
    name,
    category: info.category,
    proficiency: info.proficiency,
    matchScore: required.some(r => r.toLowerCase() === name) ? 1 : 0.5,
    priority: i + 1,
    highlighted: required.some(r => r.toLowerCase() === name) && info.proficiency >= 4,
  }))
}

function buildSections(request: GenerationRequest, projects: ProjectRanking[], skills: PrioritizedSkill[]): ResumeSection[] {
  const sections: ResumeSection[] = []

  sections.push(buildSummarySection(request, skills))
  sections.push(buildSkillsSection(skills))
  sections.push(buildExperienceSection(request))
  sections.push(buildProjectsSection(projects, request))
  sections.push(buildEducationSection(request))
  sections.push(buildCertificationsSection(request))

  return sections
}

function buildSummarySection(request: GenerationRequest, skills: PrioritizedSkill[]): ResumeSection {
  const topSkills = skills.filter(s => s.highlighted).slice(0, 5).map(s => s.name)
  const summaryText = generateSummary(request, skills)

  return {
    id: v4Service.generate('sec'),
    type: 'summary',
    title: 'Professional Summary',
    items: [{
      id: v4Service.generate('item'), title: 'Summary', subtitle: '', dateRange: null,
      description: summaryText,
      bullets: [summaryText],
      relevance: 1, skills: topSkills,
    }],
    relevance: 1,
    included: true,
  }
}

function buildSkillsSection(skills: PrioritizedSkill[]): ResumeSection {
  return {
    id: v4Service.generate('sec'),
    type: 'skills',
    title: 'Technical Skills',
    items: skills.map(s => ({
      id: v4Service.generate('item'),
      title: s.name,
      subtitle: s.category,
      dateRange: null,
      description: `Proficiency: ${s.proficiency}/5`,
      bullets: [],
      relevance: s.matchScore,
      skills: [s.name],
    })),
    relevance: 1,
    included: skills.length > 0,
  }
}

function buildExperienceSection(request: GenerationRequest): ResumeSection {
  const items: ResumeSectionItem[] = []
  if (request.experienceLevel) {
    const years = parseInt(request.experienceLevel) || 0
    items.push({
      id: v4Service.generate('item'), title: 'Professional Experience', subtitle: `${years}+ years`, dateRange: null,
      description: `Experienced professional with ${years}+ years in ${request.companyIndustry || 'technology'} industry.`,
      bullets: [
        `Delivered production systems serving ${request.remote ? 'remote' : 'on-site'} stakeholders`,
        `Applied ${request.requiredSkills.slice(0, 3).join(', ')} across multiple projects`,
        'Collaborated with cross-functional teams to drive technical initiatives',
      ],
      relevance: 1, skills: request.requiredSkills.slice(0, 5),
    })
  }
  return { id: v4Service.generate('sec'), type: 'experience', title: 'Experience', items, relevance: items.length > 0 ? 1 : 0, included: items.length > 0 }
}

function buildProjectsSection(projects: ProjectRanking[], request: GenerationRequest): ResumeSection {
  const relevant = projects.filter(p => p.included && p.overallScore > 0.3).slice(0, 3)
  return {
    id: v4Service.generate('sec'),
    type: 'projects',
    title: 'Projects',
    items: relevant.map(p => ({
      id: v4Service.generate('item'), title: p.name, subtitle: p.technologies.join(', '), dateRange: null,
      description: p.description,
      bullets: buildProjectBullets(p, request),
      relevance: p.overallScore, skills: p.technologies,
    })),
    relevance: relevant.length > 0 ? 1 : 0,
    included: relevant.length > 0,
  }
}

function buildProjectBullets(project: ProjectRanking, request: GenerationRequest): string[] {
  const bullets: string[] = []
  const matchedTech = project.technologies.filter(t => request.requiredSkills.some(s => s.toLowerCase() === t.toLowerCase()))
  if (matchedTech.length > 0) {
    bullets.push(`Built with ${matchedTech.slice(0, 3).join(', ')}`)
  }
  if (project.impact > 0.5) {
    bullets.push('Delivered measurable impact through technical execution')
  }
  bullets.push(`Applied ${request.companyIndustry || 'industry'} domain knowledge`)
  return bullets
}

function buildEducationSection(request: GenerationRequest): ResumeSection {
  const included = !!request.educationRequired
  return {
    id: v4Service.generate('sec'),
    type: 'education',
    title: 'Education',
    items: included ? [{
      id: v4Service.generate('item'), title: request.educationRequired, subtitle: '', dateRange: null,
      description: `Qualification in ${request.companyIndustry || 'relevant field'}`,
      bullets: [],
      relevance: 1, skills: [],
    }] : [],
    relevance: included ? 1 : 0,
    included,
  }
}

function buildCertificationsSection(request: GenerationRequest): ResumeSection {
  const included = request.certificationsRequired.length > 0
  return {
    id: v4Service.generate('sec'),
    type: 'certifications',
    title: 'Certifications',
    items: request.certificationsRequired.map(c => ({
      id: v4Service.generate('item'), title: c, subtitle: '', dateRange: null,
      description: `Professional certification`,
      bullets: [], relevance: 1, skills: [],
    })),
    relevance: included ? 1 : 0,
    included,
  }
}

function determineOrdering(sections: ResumeSection[], request: GenerationRequest): SectionOrder[] {
  const mode = request.experienceLevel ? 'ats_first' : 'chronological'
  const ordered = [...sections].filter(s => s.included)

  if (mode === 'ats_first') {
    const priority: Record<string, number> = { summary: 0, skills: 1, experience: 2, projects: 3, education: 4, certifications: 5 }
    ordered.sort((a, b) => (priority[a.type] ?? 99) - (priority[b.type] ?? 99))
  }

  return ordered.map((s, i) => ({ sectionId: s.id, position: i }))
}

export function generateSummary(request: GenerationRequest, skills: PrioritizedSkill[]): string {
  const topSkills = skills.filter(s => s.highlighted).slice(0, 5).map(s => s.name)
  const skillStr = topSkills.length > 0 ? topSkills.slice(0, 3).join(', ') + (topSkills.length > 3 ? ' and more' : '') : 'software development'
  const industry = request.companyIndustry || 'technology'
  const experience = request.experienceLevel ? `${request.experienceLevel}+ years of` : 'Proven'
  return `${experience} experience in ${industry} with expertise in ${skillStr}. Passionate about building scalable solutions and driving technical excellence. Strong background in delivering production-ready systems.`
}

export function calculateATSScore(skills: PrioritizedSkill[], missing: string[], sections: ResumeSection[]): number {
  const skillScore = skills.length > 0 ? (skills.filter(s => s.matchScore > 0.7).length / skills.length) * 40 : 0
  const missingScore = missing.length === 0 ? 20 : Math.max(0, 20 - missing.length * 4)
  const sectionScore = sections.filter(s => s.included).length >= 4 ? 20 : sections.filter(s => s.included).length * 5
  const bulletScore = sections.some(s => s.items.some(i => i.bullets.some(b => ATS_KEYWORDS.some(k => b.toLowerCase().includes(k))))) ? 20 : 10
  return Math.round(skillScore + missingScore + sectionScore + bulletScore)
}

export function findMissingKeywords(required: string[], skills: PrioritizedSkill[]): string[] {
  const skillNames = new Set(skills.map(s => s.name.toLowerCase()))
  return required.filter(s => !skillNames.has(s.toLowerCase()))
}

export function generateImprovements(missing: string[], wordCount: number): string[] {
  const improvements: string[] = []
  if (missing.length > 0) improvements.push(`Add missing keywords: ${missing.slice(0, 5).join(', ')}`)
  if (wordCount < 300) improvements.push('Consider adding more detail to reach target length')
  if (wordCount > 800) improvements.push('Resume is too long; consider trimming to fit one page')
  return improvements
}

export function improveBullets(bullets: string[]): string[] {
  return bullets.map(b => {
    let improved = b.charAt(0).toUpperCase() + b.slice(1)
    const hasAction = ACTION_VERBS.some(v => improved.toLowerCase().startsWith(v))
    if (!hasAction) improved = 'Implemented ' + improved.charAt(0).toLowerCase() + improved.slice(1)
    if (improved.length < 50) improved += ' resulting in improved system performance'
    return improved
  })
}

export function enhanceActionVerbs(text: string): string {
  const replacements: [RegExp, string][] = [
    [/was responsible for/g, 'led'],
    [/was in charge of/g, 'managed'],
    [/worked on/g, 'developed'],
    [/helped with/g, 'contributed to'],
    [/was part of/g, 'collaborated on'],
    [/made/g, 'created'],
    [/did/g, 'executed'],
    [/got/g, 'achieved'],
    [/used/g, 'leveraged'],
    [/gave/g, 'presented'],
  ]
  let result = text
  for (const [pattern, replacement] of replacements) {
    result = result.replace(pattern, replacement)
  }
  return result
}

export function optimizeForATS(text: string, keywords: string[]): string {
  let result = text
  for (const kw of keywords) {
    const lower = kw.toLowerCase()
    if (!result.toLowerCase().includes(lower)) {
      result += ` Proficient in ${kw}.`
    }
  }
  return result
}

export function trimToLength(text: string, maxChars: number): string {
  if (text.length <= maxChars) return text
  return text.slice(0, text.lastIndexOf('.', maxChars) + 1) || text.slice(0, maxChars) + '...'
}
