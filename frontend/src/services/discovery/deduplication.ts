import type { Job, DuplicateGroup, DuplicateMatchType } from './types'

interface DuplicateCandidate {
  job: Job
  matchType: DuplicateMatchType
  reasons: string[]
}

function jaccardSimilarity(a: Set<string>, b: Set<string>): number {
  if (a.size === 0 && b.size === 0) return 1
  const intersection = new Set([...a].filter(x => b.has(x)))
  const union = new Set([...a, ...b])
  return intersection.size / union.size
}

function titleSimilarity(a: string, b: string): number {
  const aWords = new Set(a.toLowerCase().split(/\s+/))
  const bWords = new Set(b.toLowerCase().split(/\s+/))
  return jaccardSimilarity(aWords, bWords)
}

function locationSimilarity(a: string, b: string): number {
  if (!a || !b) return 0.5
  const aParts = new Set(a.toLowerCase().split(/[,;]\s*/).map(s => s.trim()))
  const bParts = new Set(b.toLowerCase().split(/[,;]\s*/).map(s => s.trim()))
  return jaccardSimilarity(aParts, bParts)
}

function findDuplicateCandidates(jobs: Job[], index: number): DuplicateCandidate[] {
  const job = jobs[index]
  const candidates: DuplicateCandidate[] = []

  for (let i = 0; i < index; i++) {
    const other = jobs[i]
    const reasons: string[] = []
    let matchType: DuplicateMatchType = 'low_confidence'

    if (job.externalId === other.externalId && job.provider === other.provider) {
      reasons.push('same external id')
      matchType = 'exact'
    } else if (job.sourceUrl === other.sourceUrl) {
      reasons.push('same source url')
      matchType = 'exact'
    } else if (job.normalizedTitle === other.normalizedTitle && job.normalizedCompany === other.normalizedCompany) {
      reasons.push('same title and company')
      const locSim = locationSimilarity(job.location, other.location)
      if (locSim >= 0.8) {
        reasons.push('similar location')
        matchType = 'high_confidence'
      } else {
        matchType = 'medium_confidence'
      }
    } else if (job.normalizedCompany === other.normalizedCompany) {
      const titleSim = titleSimilarity(job.title, other.title)
      if (titleSim >= 0.8) {
        reasons.push(`similar title (${Math.round(titleSim * 100)}%)`)
        matchType = 'medium_confidence'
      }
    }

    if (matchType !== 'low_confidence') {
      candidates.push({ job: other, matchType, reasons })
    }
  }

  return candidates
}

export function deduplicate(jobs: Job[]): { unique: Job[]; duplicates: DuplicateGroup[] } {
  const unique: Job[] = []
  const duplicateGroups: DuplicateGroup[] = []

  for (let i = 0; i < jobs.length; i++) {
    const candidates = findDuplicateCandidates(jobs, i)
    if (candidates.length > 0) {
      const bestMatch = candidates.reduce((a, b) => {
        const order = ['exact', 'high_confidence', 'medium_confidence', 'low_confidence']
        return order.indexOf(a.matchType) <= order.indexOf(b.matchType) ? a : b
      })
      const existingGroup = duplicateGroups.find(g => g.masterJob.id === bestMatch.job.id)
      if (existingGroup) {
        existingGroup.duplicates.push(jobs[i])
      } else {
        duplicateGroups.push({
          masterJob: bestMatch.job,
          duplicates: [jobs[i]],
          matchType: bestMatch.matchType,
          matchReasons: bestMatch.reasons,
        })
      }
    } else {
      unique.push(jobs[i])
    }
  }

  return { unique, duplicates: duplicateGroups }
}

export function countDuplicates(jobs: Job[]): number {
  return jobs.length - deduplicate(jobs).unique.length
}
