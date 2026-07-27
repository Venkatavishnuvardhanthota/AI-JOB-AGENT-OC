import type { MatchResult, CandidateProfile, MatchWeights, MatchStatistics, Decision } from './types'
import type { Job } from '@/services/discovery/types'
import { scoreJob } from './scoring'
import { rankByMatch } from './ranking'
import { matchHistoryService } from './history'

let profileCache: CandidateProfile | null = null

export const matchingService = {
  setProfile(profile: CandidateProfile): void {
    profileCache = profile
  },

  getProfile(): CandidateProfile | null {
    return profileCache
  },

  scoreSingleJob(job: Job, profile: CandidateProfile, resumeId: string | null, weights?: MatchWeights): MatchResult {
    const result = scoreJob(job, profile, resumeId, weights)
    matchHistoryService.add({
      id: `mh_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      jobId: job.id,
      jobTitle: job.title,
      company: job.company,
      overall: result.overall,
      decision: result.decision,
      resumeId,
      scoredAt: result.scoredAt,
    })
    return result
  },

  scoreBatch(jobs: Job[], profile: CandidateProfile, resumeId: string | null, weights?: MatchWeights): MatchResult[] {
    const results: MatchResult[] = []
    for (const job of jobs) {
      results.push(this.scoreSingleJob(job, profile, resumeId, weights))
    }
    return rankByMatch(results)
  },

  scoreBatchCached(jobs: Job[], profile: CandidateProfile, resumeId: string | null, weights?: MatchWeights): MatchResult[] {
    const cache = getMatchCache()
    const toScore: Job[] = []
    const cached: MatchResult[] = []

    for (const job of jobs) {
      const cachedResult = cache.get(job.id)
      if (cachedResult) {
        cached.push(cachedResult)
      } else {
        toScore.push(job)
      }
    }

    const newlyScored = toScore.map(job => this.scoreSingleJob(job, profile, resumeId, weights))
    for (const result of newlyScored) {
      cache.set(result.jobId, result)
    }

    saveMatchCache(cache)

    return rankByMatch([...cached, ...newlyScored])
  },

  getStatistics(results: MatchResult[]): MatchStatistics {
    if (results.length === 0) {
      return {
        totalScored: 0, averageScore: 0, averageConfidence: 0,
        decisionBreakdown: {} as Record<Decision, number>,
        averageSkillScore: 0, averageExperienceScore: 0,
        averageSalaryScore: 0, averageLocationScore: 0,
        topSkills: [], commonMissingSkills: [],
      }
    }

    const decisionBreakdown: Record<string, number> = {}
    const skillCount: Record<string, number> = {}
    const missingSkillCount: Record<string, number> = {}

    for (const r of results) {
      decisionBreakdown[r.decision] = (decisionBreakdown[r.decision] || 0) + 1
      for (const skill of r.job.requiredSkills) {
        skillCount[skill] = (skillCount[skill] || 0) + 1
      }
      for (const skill of r.missingSkills) {
        missingSkillCount[skill] = (missingSkillCount[skill] || 0) + 1
      }
    }

    return {
      totalScored: results.length,
      averageScore: Math.round((results.reduce((s, r) => s + r.overall, 0) / results.length) * 1000) / 1000,
      averageConfidence: Math.round((results.reduce((s, r) => s + r.confidence, 0) / results.length) * 1000) / 1000,
      decisionBreakdown: decisionBreakdown as Record<Decision, number>,
      averageSkillScore: Math.round((results.reduce((s, r) => s + r.skillScore, 0) / results.length) * 1000) / 1000,
      averageExperienceScore: Math.round((results.reduce((s, r) => s + r.experienceScore, 0) / results.length) * 1000) / 1000,
      averageSalaryScore: Math.round((results.reduce((s, r) => s + r.salaryScore, 0) / results.length) * 1000) / 1000,
      averageLocationScore: Math.round((results.reduce((s, r) => s + r.locationScore, 0) / results.length) * 1000) / 1000,
      topSkills: Object.entries(skillCount).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([skill, count]) => ({ skill, count })),
      commonMissingSkills: Object.entries(missingSkillCount).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([skill, count]) => ({ skill, count })),
    }
  },

  clearCache(): void {
    profileCache = null
    localStorage.removeItem('ajapp_match_cache')
  },
}

const CACHE_PREFIX = 'ajapp_match_'

function getMatchCache(): Map<string, MatchResult> {
  try {
    const raw = localStorage.getItem(`${CACHE_PREFIX}cache`)
    if (!raw) return new Map()
    const parsed = JSON.parse(raw) as [string, MatchResult][]
    return new Map(parsed)
  } catch { return new Map() }
}

function saveMatchCache(cache: Map<string, MatchResult>): void {
  try {
    const entries = [...cache.entries()]
    localStorage.setItem(`${CACHE_PREFIX}cache`, JSON.stringify(entries))
  } catch {}
}
