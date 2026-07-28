import type { ProviderId, Job, RawJob, DuplicateGroup } from '../discovery/types'
import { normalizeJobs } from '../discovery/normalization'
import { deduplicate } from '../discovery/deduplication'
import type { ProviderRoutingDecision } from './routing-types'

interface AggregatedSource {
  providerId: ProviderId
  jobs: RawJob[]
}

export function aggregateResults(
  sources: AggregatedSource[],
  decisions: ProviderRoutingDecision[],
  queryKeywords: string
): { jobs: Job[]; duplicates: DuplicateGroup[]; normalizedCount: number } {
  const allNormalized: Job[] = []

  for (const source of sources) {
    if (source.jobs.length === 0) continue
    const sourceUrl = `https://${source.providerId}.com/search?q=${encodeURIComponent(queryKeywords)}`
    const normalized = normalizeJobs(source.jobs, source.providerId, sourceUrl)
    allNormalized.push(...normalized)
  }

  const allRanked = rankByQuality(allNormalized, decisions)

  const { unique, duplicates } = deduplicate(allRanked)

  return { jobs: unique, duplicates, normalizedCount: allNormalized.length }
}

function rankByQuality(jobs: Job[], decisions: ProviderRoutingDecision[]): Job[] {
  const priorityMap = new Map<ProviderId, number>()
  const reliabilityMap = new Map<ProviderId, number>()

  for (const d of decisions) {
    priorityMap.set(d.providerId, d.priority)
    reliabilityMap.set(d.providerId, d.metadata?.reliabilityScore ?? 0.5)
  }

  return jobs.sort((a, b) => {
    const aReliability = reliabilityMap.get(a.provider) ?? 0.5
    const bReliability = reliabilityMap.get(b.provider) ?? 0.5

    if (Math.abs(aReliability - bReliability) > 0.1) {
      return bReliability - aReliability
    }

    const aPriority = priorityMap.get(a.provider) ?? 100
    const bPriority = priorityMap.get(b.provider) ?? 100
    return aPriority - bPriority
  })
}
