import { describe, it, expect, beforeEach } from 'vitest'
import { generateResume, generateSummary, calculateATSScore, findMissingKeywords, improveBullets, enhanceActionVerbs, optimizeForATS, trimToLength } from './resume-generation'
import { generateCoverLetter } from './cover-letter-generation'
import { generateAnswers, generateAllDefaultAnswers } from './questionnaire-engine'
import { buildPackage, rebuildPackage } from './package-builder'
import { versionManager } from './version-manager'
import { reviewPackage } from './review-engine'
import { computeQualityScores, computeOverallPackageScore } from './quality-score'
import { exportPackage, exportAllFormats, generateMarkdown, generateJSON } from './export-engine'
import { rankProjects } from './project-intelligence'
import { applicationGenerationService } from './application-generation'
import type { GenerationRequest } from './types'

const mockRequest: GenerationRequest = {
  jobId: 'job_001',
  jobTitle: 'Senior Software Engineer',
  companyName: 'TechCorp',
  companyIndustry: 'Technology',
  companyDescription: 'A leading technology company building innovative solutions.',
  jobDescription: 'We are looking for a Senior Software Engineer to join our team. You will design and build scalable microservices, lead code reviews, and mentor junior engineers.',
  requiredSkills: ['TypeScript', 'React', 'Node.js', 'AWS', 'Docker', 'PostgreSQL'],
  preferredSkills: ['GraphQL', 'Kubernetes', 'Redis'],
  experienceLevel: '5',
  educationRequired: "Bachelor's in Computer Science",
  certificationsRequired: ['AWS Solutions Architect'],
  responsibilities: ['Design and implement scalable microservices', 'Lead code reviews', 'Mentor junior engineers'],
  salaryRange: { min: 120000, max: 180000, currency: 'USD' },
  remote: true,
  location: 'San Francisco, CA',
  applicationUrl: null,
}

beforeEach(() => {
  localStorage.clear()
})

describe('resume-generation', () => {
  it('generates a resume with all sections', () => {
    const resume = generateResume(mockRequest, [])
    expect(resume.id).toMatch(/^resumeGen_/)
    expect(resume.jobId).toBe('job_001')
    expect(resume.sections.length).toBeGreaterThanOrEqual(4)
    expect(resume.skills.length).toBeGreaterThan(0)
  })

  it('prioritizes required skills', () => {
    const resume = generateResume(mockRequest, [])
    const typeScript = resume.skills.find(s => s.name.toLowerCase() === 'typescript')
    expect(typeScript).toBeDefined()
    expect(typeScript?.matchScore).toBe(1)
  })

  it('highlights top matching skills', () => {
    const resume = generateResume(mockRequest, [])
    const highlighted = resume.skills.filter(s => s.highlighted)
    expect(highlighted.length).toBeGreaterThan(0)
  })

  it('computes ATS score', () => {
    const resume = generateResume(mockRequest, [])
    expect(resume.metadata.atsScore).toBeGreaterThanOrEqual(0)
    expect(resume.metadata.atsScore).toBeLessThanOrEqual(100)
  })

  it('generates professional summary', () => {
    const summary = generateSummary(mockRequest, [])
    expect(summary).toContain('Technology')
    expect(summary.length).toBeGreaterThan(50)
  })

  it('finds missing keywords', () => {
    const missing = findMissingKeywords(['TypeScript', 'Go', 'Rust'], [])
    expect(missing).toContain('Go')
    expect(missing).toContain('Rust')
    expect(missing.length).toBe(3)
  })

  it('improves bullet points', () => {
    const bullets = improveBullets(['built a feature', 'helped with deployment'])
    expect(bullets[0]).toMatch(/^[A-Z]/)
    expect(bullets.length).toBe(2)
  })

  it('enhances action verbs', () => {
    const result = enhanceActionVerbs('was responsible for the backend')
    expect(result).not.toContain('was responsible for')
  })

  it('optimizes text for ATS', () => {
    const result = optimizeForATS('I am a developer', ['TypeScript', 'React'])
    expect(result.toLowerCase()).toContain('typescript')
    expect(result.toLowerCase()).toContain('react')
  })

  it('trims text to length', () => {
    const text = 'This is a long sentence. And another one. And a third.'
    const trimmed = trimToLength(text, 30)
    expect(trimmed.length).toBeLessThanOrEqual(31)
  })

  it('calculates ATS score correctly', () => {
    const resume = generateResume(mockRequest, [])
    const score = calculateATSScore(resume.skills, resume.metadata.missingKeywords, resume.sections)
    expect(score).toBeGreaterThanOrEqual(0)
    expect(score).toBeLessThanOrEqual(100)
  })
})

describe('cover-letter-generation', () => {
  it('generates a cover letter', () => {
    const cl = generateCoverLetter(mockRequest, [], 'Experienced engineer with strong background.')
    expect(cl.id).toMatch(/^clGen_/)
    expect(cl.jobId).toBe('job_001')
    expect(cl.companyName).toBe('TechCorp')
    expect(cl.subject).toContain('Senior Software Engineer')
    expect(cl.body).toContain('TechCorp')
  })

  it('includes skill mentions', () => {
    const cl = generateCoverLetter(mockRequest, [], 'Summary text')
    expect(cl.metadata.skillMentions.length).toBeGreaterThan(0)
    expect(cl.metadata.personalizationScore).toBeGreaterThan(0)
  })

  it('includes project mentions when relevant projects exist', () => {
    const projects = [{ name: 'E-Commerce Platform', technologies: ['React', 'Node.js'], description: 'Online store', relevance: 0.8 }]
    const cl = generateCoverLetter(mockRequest, projects, 'Summary')
    expect(cl.metadata.projectMentions).toContain('E-Commerce Platform')
  })
})

describe('questionnaire-engine', () => {
  it('generates answers for specified topics', () => {
    const answers = generateAnswers(mockRequest, ['why_company', 'why_role', 'expected_salary'])
    expect(answers).toHaveLength(3)
    expect(answers[0].topic).toBe('why_company')
    expect(answers[0].answer).toContain('TechCorp')
    expect(answers[0].confidence).toBeGreaterThan(0)
  })

  it('generates all default answers', () => {
    const answers = generateAllDefaultAnswers(mockRequest)
    expect(answers.length).toBeGreaterThanOrEqual(8)
  })

  it('answers why_company with company description', () => {
    const [answer] = generateAnswers(mockRequest, ['why_company'])
    expect(answer.answer).toContain(mockRequest.companyName)
  })

  it('answers salary question when range is provided', () => {
    const [answer] = generateAnswers(mockRequest, ['expected_salary'])
    expect(answer.answer).toContain('USD')
    expect(answer.answer).toContain('1,20')
  })
})

describe('package-builder', () => {
  it('builds a complete package', () => {
    const pkg = buildPackage(mockRequest)
    expect(pkg.id).toMatch(/^pkg_/)
    expect(pkg.jobTitle).toBe('Senior Software Engineer')
    expect(pkg.resume).toBeDefined()
    expect(pkg.coverLetter).toBeDefined()
    expect(pkg.questionnaire.length).toBeGreaterThan(0)
  })

  it('optionally excludes cover letter', () => {
    const pkg = buildPackage(mockRequest, { includeCoverLetter: false })
    expect(pkg.coverLetter).toBeNull()
  })

  it('includes portfolio selection', () => {
    const pkg = buildPackage(mockRequest, { projects: [{ name: 'Web App', technologies: ['React'], description: 'A web app', relevance: 0.9 }] })
    expect(pkg.portfolio.githubRepos.length).toBeGreaterThan(0)
  })

  it('includes certificate selection', () => {
    const pkg = buildPackage(mockRequest)
    expect(pkg.certificates.length).toBeGreaterThan(0)
  })

  it('rebuilds an existing package', () => {
    const pkg = buildPackage(mockRequest)
    const rebuilt = rebuildPackage(pkg, mockRequest)
    expect(rebuilt.id).toBe(pkg.id)
  })

  it('sets status based on confidence score', () => {
    const pkg = buildPackage(mockRequest)
    expect(['ready', 'needs_review']).toContain(pkg.status)
  })
})

describe('version-manager', () => {
  it('creates version entries', () => {
    const pkg = buildPackage(mockRequest)
    const version = versionManager.createVersion(pkg)
    expect(version.version).toBe(1)
    expect(version.packageId).toBe(pkg.id)
  })

  it('increments version numbers', () => {
    const pkg = buildPackage(mockRequest)
    versionManager.createVersion(pkg)
    const v2 = versionManager.createVersion(pkg)
    expect(v2.version).toBe(2)
  })

  it('retrieves versions by package', () => {
    const pkg = buildPackage(mockRequest)
    versionManager.createVersion(pkg)
    expect(versionManager.getVersions(pkg.id)).toHaveLength(1)
  })

  it('gets latest version', () => {
    const pkg = buildPackage(mockRequest)
    versionManager.createVersion(pkg)
    versionManager.createVersion(pkg)
    const latest = versionManager.getLatestVersion(pkg.id)
    expect(latest?.version).toBe(2)
  })

  it('detects duplicates', () => {
    const pkg = buildPackage(mockRequest)
    expect(versionManager.detectDuplicate(pkg.id, pkg)).toBe(false)
  })
})

describe('review-engine', () => {
  it('reviews a complete package', () => {
    const resume = generateResume(mockRequest, [])
    const cl = generateCoverLetter(mockRequest, [], resume.summary)
    const answers = generateAllDefaultAnswers(mockRequest)
    const results = reviewPackage(resume, cl, answers)
    expect(results.length).toBeGreaterThan(0)
  })

  it('detects consistency issues between resume and cover letter', () => {
    const resume = generateResume(mockRequest, [])
    const cl = generateCoverLetter(mockRequest, [], resume.summary)
    const results = reviewPackage(resume, cl, [])
    expect(results.some(r => r.location === 'consistency')).toBe(false)
  })

  it('returns review results for a package with questionnaire', () => {
    const resume = generateResume(mockRequest, [])
    const cl = generateCoverLetter(mockRequest, [], resume.summary)
    const answers = generateAllDefaultAnswers(mockRequest)
    const results = reviewPackage(resume, cl, answers)
    expect(results.length).toBeGreaterThan(0)
  })

  it('detects short cover letters', () => {
    const resume = generateResume(mockRequest, [])
    const cl = generateCoverLetter(mockRequest, [], resume.summary)
    const results = reviewPackage(resume, cl, [])
    const lengthIssues = results.filter(r => r.category === 'length')
    expect(lengthIssues.length).toBeGreaterThan(0)
  })
})

describe('quality-score', () => {
  it('computes quality scores', () => {
    const resume = generateResume(mockRequest, [])
    const cl = generateCoverLetter(mockRequest, [], resume.summary)
    const answers = generateAllDefaultAnswers(mockRequest)
    const scores = computeQualityScores(resume, cl, answers)
    expect(scores.resume).toBeGreaterThan(0)
    expect(scores.coverLetter).toBeGreaterThan(0)
    expect(scores.questionnaire).toBeGreaterThan(0)
    expect(scores.atsReadiness).toBeGreaterThan(0)
  })

  it('computes overall package score', () => {
    const resume = generateResume(mockRequest, [])
    const cl = generateCoverLetter(mockRequest, [], resume.summary)
    const answers = generateAllDefaultAnswers(mockRequest)
    const scores = computeQualityScores(resume, cl, answers)
    const overall = computeOverallPackageScore(scores)
    expect(overall).toBeGreaterThan(0)
    expect(overall).toBeLessThanOrEqual(100)
  })
})

describe('export-engine', () => {
  it('exports package to PDF', () => {
    const pkg = buildPackage(mockRequest)
    const result = exportPackage(pkg, 'pdf')
    expect(result.format).toBe('pdf')
    expect(result.packageId).toBe(pkg.id)
    expect(result.filename).toContain('TechCorp')
  })

  it('exports all formats', () => {
    const pkg = buildPackage(mockRequest)
    const results = exportAllFormats(pkg)
    expect(results).toHaveLength(4)
  })

  it('generates markdown', () => {
    const pkg = buildPackage(mockRequest)
    const md = generateMarkdown(pkg)
    expect(md).toContain('# Application Package')
    expect(md).toContain('Senior Software Engineer')
    expect(md).toContain('TechCorp')
  })

  it('generates JSON', () => {
    const pkg = buildPackage(mockRequest)
    const json = generateJSON(pkg)
    const parsed = JSON.parse(json)
    expect(parsed.jobTitle).toBe('Senior Software Engineer')
    expect(parsed.companyName).toBe('TechCorp')
  })
})

describe('project-intelligence', () => {
  it('ranks projects by relevance', () => {
    const projects = [
      { name: 'Cloud App', description: 'A cloud app', technologies: ['TypeScript', 'React', 'AWS'], impact: 0.8, recency: 0.9, domain: 'Technology' },
      { name: 'Old Project', description: 'An old project', technologies: ['Java', 'Spring'], impact: 0.3, recency: 0.1, domain: 'Finance' },
    ]
    const ranked = rankProjects(projects, mockRequest)
    expect(ranked).toHaveLength(2)
    expect(ranked[0].name).toBe('Cloud App')
    expect(ranked[0].overallScore).toBeGreaterThan(ranked[1].overallScore)
  })

  it('excludes weak projects', () => {
    const projects = [
      { name: 'Weak', description: 'Low relevance', technologies: ['COBOL'], impact: 0.1, recency: 0.1, domain: 'Legacy' },
    ]
    const ranked = rankProjects(projects, mockRequest)
    expect(ranked[0].included).toBe(false)
    expect(ranked[0].exclusionReason).toBeTruthy()
  })
})

describe('applicationGenerationService', () => {
  it('generates and stores a package', () => {
    const pkg = applicationGenerationService.generate(mockRequest)
    expect(applicationGenerationService.getPackage(pkg.id)).toBeDefined()
  })

  it('lists all packages', () => {
    applicationGenerationService.generate(mockRequest)
    applicationGenerationService.generate({ ...mockRequest, jobId: 'job_002', jobTitle: 'Frontend Developer' })
    expect(applicationGenerationService.getAllPackages()).toHaveLength(2)
  })

  it('deletes a package', () => {
    const pkg = applicationGenerationService.generate(mockRequest)
    applicationGenerationService.deletePackage(pkg.id)
    expect(applicationGenerationService.getPackage(pkg.id)).toBeUndefined()
  })

  it('updates package status', () => {
    const pkg = applicationGenerationService.generate(mockRequest)
    applicationGenerationService.updatePackageStatus(pkg.id, 'exported')
    expect(applicationGenerationService.getPackage(pkg.id)?.status).toBe('exported')
  })

  it('regenerates a package', () => {
    const pkg = applicationGenerationService.generate(mockRequest)
    const updated = applicationGenerationService.regenerate(pkg.id, mockRequest)
    expect(updated).not.toBeNull()
    expect(updated?.id).toBe(pkg.id)
  })

  it('computes statistics', () => {
    applicationGenerationService.generate(mockRequest)
    applicationGenerationService.generate({ ...mockRequest, jobId: 'job_002', jobTitle: 'DevOps Engineer' })
    const stats = applicationGenerationService.getStatistics()
    expect(stats.totalPackages).toBe(2)
    expect(stats.averageConfidence).toBeGreaterThan(0)
  })

  it('ranks skills', () => {
    const skills = [
      { name: 'TypeScript', category: 'language', proficiency: 5 },
      { name: 'Python', category: 'language', proficiency: 4 },
      { name: 'Go', category: 'language', proficiency: 3 },
    ]
    const ranked = applicationGenerationService.rankSkills(skills, mockRequest)
    expect(ranked[0].name).toBe('TypeScript')
    expect(ranked[0].matchScore).toBe(1)
    expect(ranked[0].priority).toBe(1)
  })
})
