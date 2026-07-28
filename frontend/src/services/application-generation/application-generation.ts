import type { GenerationRequest, ApplicationPackage, GenerationStatistics, ProjectRanking, ExportFormat, ExportResult, VersionEntry, ReviewResult } from './types'
import { buildPackage, rebuildPackage } from './package-builder'
import { versionManager } from './version-manager'
import { exportPackage, exportAllFormats } from './export-engine'
import { computeOverallPackageScore } from './quality-score'


const PREFIX = 'ajapp_gen_'

function get<T>(key: string, fallback: T): T {
  try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback } catch { return fallback }
}
function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

export const applicationGenerationService = {
  generate(request: GenerationRequest, options?: { includeCoverLetter?: boolean; projects?: { name: string; technologies: string[]; description: string; relevance: number }[] }): ApplicationPackage {
    const pkg = buildPackage(request, options)
    this.savePackage(pkg)
    versionManager.createVersion(pkg)
    return pkg
  },

  regenerate(packageId: string, request: GenerationRequest): ApplicationPackage | null {
    const existing = this.getPackage(packageId)
    if (!existing) return null
    const pkg = rebuildPackage(existing, request)
    this.savePackage(pkg)
    versionManager.createVersion(pkg)
    return pkg
  },

  getPackage(id: string): ApplicationPackage | undefined {
    return this.getAllPackages().find(p => p.id === id)
  },

  getAllPackages(): ApplicationPackage[] {
    return get<ApplicationPackage[]>(`${PREFIX}packages`, [])
  },

  savePackage(pkg: ApplicationPackage): void {
    const packages = this.getAllPackages()
    const idx = packages.findIndex(p => p.id === pkg.id)
    if (idx !== -1) {
      packages[idx] = { ...pkg, updatedAt: new Date().toISOString() }
    } else {
      packages.unshift(pkg)
    }
    set(`${PREFIX}packages`, packages.slice(0, 200))
  },

  deletePackage(id: string): void {
    const packages = this.getAllPackages().filter(p => p.id !== id)
    set(`${PREFIX}packages`, packages)
  },

  updatePackageStatus(id: string, status: ApplicationPackage['status']): void {
    const pkg = this.getPackage(id)
    if (pkg) {
      pkg.status = status
      pkg.updatedAt = new Date().toISOString()
      this.savePackage(pkg)
    }
  },

  getStatistics(): GenerationStatistics {
    const packages = this.getAllPackages()
    const scored = packages.filter(p => p.metadata.confidenceScore > 0)
    return {
      totalPackages: packages.length,
      readyToApply: packages.filter(p => p.status === 'ready').length,
      needsReview: packages.filter(p => p.status === 'needs_review').length,
      averageConfidence: scored.length > 0 ? Math.round(scored.reduce((s, p) => s + p.metadata.confidenceScore, 0) / scored.length) : 0,
      averageResumeScore: scored.length > 0 ? Math.round(scored.reduce((s, p) => s + p.metadata.qualityScores.resume, 0) / scored.length) : 0,
      averageCoverLetterScore: scored.filter(p => p.metadata.qualityScores.coverLetter !== null).length > 0
        ? Math.round(scored.filter(p => p.metadata.qualityScores.coverLetter !== null).reduce((s, p) => s + (p.metadata.qualityScores.coverLetter ?? 0), 0) / scored.filter(p => p.metadata.qualityScores.coverLetter !== null).length) : 0,
      averagePackageScore: scored.length > 0 ? Math.round(scored.reduce((s, p) => s + computeOverallPackageScore(p.metadata.qualityScores), 0) / scored.length) : 0,
      recentPackages: packages.slice(0, 5),
      generationTrend: computeTrend(packages),
    }
  },

  rankProjects(projects: { name: string; description: string; technologies: string[]; impact: number; recency: number; domain: string }[], request: GenerationRequest): ProjectRanking[] {
    return projects.map(p => {
      const techOverlap = p.technologies.filter(t => request.requiredSkills.some(s => s.toLowerCase() === t.toLowerCase())).length / Math.max(p.technologies.length, 1)
      const domainMatch = p.domain.toLowerCase() === (request.companyIndustry || '').toLowerCase() ? 1 : 0.3
      const overallScore = techOverlap * 0.4 + p.impact * 0.3 + p.recency * 0.2 + domainMatch * 0.1
      return {
        name: p.name,
        description: p.description,
        technologies: p.technologies,
        relevance: techOverlap,
        impact: p.impact,
        recency: p.recency,
        domainMatch,
        overallScore,
        included: overallScore > 0.3,
        exclusionReason: overallScore <= 0.3 ? 'Low relevance to job requirements' : null,
      }
    }).sort((a, b) => b.overallScore - a.overallScore)
  },

  rankSkills(skills: { name: string; category: string; proficiency: number }[], request: GenerationRequest): { name: string; category: string; proficiency: number; matchScore: number; priority: number }[] {
    return skills.map(s => {
      const matchScore = request.requiredSkills.some(r => r.toLowerCase() === s.name.toLowerCase()) ? 1
        : request.preferredSkills.some(p => p.toLowerCase() === s.name.toLowerCase()) ? 0.7 : 0.3
      return { ...s, matchScore, priority: 0 }
    }).sort((a, b) => b.matchScore - a.matchScore)
      .map((s, i) => ({ ...s, priority: i + 1 }))
  },

  exportPackage(pkg: ApplicationPackage, format: ExportFormat): ExportResult {
    const result = exportPackage(pkg, format)
    pkg.metadata.exported = true
    if (!pkg.metadata.exportFormats.includes(format)) {
      pkg.metadata.exportFormats.push(format)
    }
    this.savePackage(pkg)
    return result
  },

  exportAll(pkg: ApplicationPackage): ExportResult[] {
    return exportAllFormats(pkg)
  },

  getVersions(packageId: string): VersionEntry[] {
    return versionManager.getVersions(packageId)
  },

  compareVersions(packageId: string, v1Id: string, v2Id: string) {
    return versionManager.compareVersions(packageId, v1Id, v2Id)
  },

  getReviews(packageId: string): ReviewResult[] {
    const pkg = this.getPackage(packageId)
    return pkg?.metadata.reviewResults ?? []
  },
}

function computeTrend(packages: ApplicationPackage[]): { date: string; count: number }[] {
  const byDate = new Map<string, number>()
  for (const pkg of packages) {
    const date = pkg.createdAt.split('T')[0]
    byDate.set(date, (byDate.get(date) || 0) + 1)
  }
  return Array.from(byDate.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-14)
    .map(([date, count]) => ({ date, count }))
}
