import type { ApplicationPackage, VersionEntry, GenerationStatus } from './types'
import { v4Service } from './utils'

const PREFIX = 'ajapp_gen_ver_'

function get<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch { return fallback }
}

function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

export const versionManager = {
  createVersion(pkg: ApplicationPackage): VersionEntry {
    const versions = this.getVersions(pkg.id)
    const latest = versions.length > 0 ? Math.max(...versions.map(v => v.version)) : 0
    const entry: VersionEntry = {
      id: v4Service.generate('ver'),
      packageId: pkg.id,
      version: latest + 1,
      status: pkg.status,
      confidenceScore: pkg.metadata.confidenceScore,
      createdAt: new Date().toISOString(),
      parentVersionId: versions.length > 0 ? versions[versions.length - 1].id : null,
      changes: this.computeChanges(versions.length > 0 ? versions[versions.length - 1] : null, pkg),
    }
    versions.push(entry)
    set(`${PREFIX}${pkg.id}`, versions)
    return entry
  },

  getVersions(packageId: string): VersionEntry[] {
    return get<VersionEntry[]>(`${PREFIX}${packageId}`, [])
  },

  getVersion(packageId: string, versionId: string): VersionEntry | undefined {
    return this.getVersions(packageId).find(v => v.id === versionId)
  },

  getLatestVersion(packageId: string): VersionEntry | undefined {
    const versions = this.getVersions(packageId)
    return versions.length > 0 ? versions.reduce((a, b) => a.version > b.version ? a : b) : undefined
  },

  updateVersionStatus(packageId: string, version: number, status: GenerationStatus): void {
    const versions = this.getVersions(packageId)
    const idx = versions.findIndex(v => v.version === version)
    if (idx !== -1) {
      versions[idx].status = status
      set(`${PREFIX}${packageId}`, versions)
    }
  },

  restoreVersion(packageId: string, versionId: string): VersionEntry | null {
    const version = this.getVersion(packageId, versionId)
    if (!version) return null
    return this.createVersion({
      metadata: { ...this.getDummyMetadata(), version: 0, confidenceScore: version.confidenceScore },
    } as unknown as ApplicationPackage)
  },

  compareVersions(packageId: string, v1Id: string, v2Id: string): { changes: string[] } {
    const v1 = this.getVersion(packageId, v1Id)
    const v2 = this.getVersion(packageId, v2Id)
    if (!v1 || !v2) return { changes: [] }

    const changes: string[] = []
    if (v1.status !== v2.status) changes.push(`Status changed from ${v1.status} to ${v2.status}`)
    if (v1.confidenceScore !== v2.confidenceScore) changes.push(`Confidence changed from ${v1.confidenceScore} to ${v2.confidenceScore}`)
    changes.push(...v2.changes)
    return { changes }
  },

  detectDuplicate(packageId: string, newPkg: ApplicationPackage): boolean {
    const versions = this.getVersions(packageId)
    if (versions.length === 0) return false
    const latest = this.getLatestVersion(packageId)
    if (!latest) return false
    return Math.abs(latest.confidenceScore - newPkg.metadata.confidenceScore) < 1
  },

  clearVersions(packageId: string): void {
    set(`${PREFIX}${packageId}`, [])
  },

  computeChanges(previous: VersionEntry | null, current: ApplicationPackage): string[] {
    const changes: string[] = []
    if (!previous) return ['Initial version']
    if (previous.confidenceScore !== current.metadata.confidenceScore) {
      const diff = current.metadata.confidenceScore - previous.confidenceScore
      changes.push(`Confidence score ${diff >= 0 ? 'improved' : 'decreased'} by ${Math.abs(diff)} points`)
    }
    return changes
  },

  getDummyMetadata() {
    return { confidenceScore: 0, qualityScores: { resume: 0, coverLetter: 0, questionnaire: 0, package: 0, atsReadiness: 0, professionalTone: 0, completeness: 0 }, reviewResults: [], generationTime: 0, version: 0, exported: false, exportFormats: [] }
  },
}
