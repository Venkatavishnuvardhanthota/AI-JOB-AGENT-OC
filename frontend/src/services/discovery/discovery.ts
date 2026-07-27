import type { Job, DiscoveryResult, SearchParams, DiscoveryError, ProviderId } from './types'
import { providerRegistry } from './provider-registry'
import { normalizeJobs } from './normalization'
import { deduplicate } from './deduplication'
import { discoveryHistoryService } from './discovery-history'
import { providerHealthService } from './provider-health'

let discoveryCounter = 0

export const discoveryService = {
  async search(
    params: SearchParams,
    options?: { providers?: ProviderId[]; profileId?: string }
  ): Promise<DiscoveryResult> {
    discoveryCounter++
    const start = Date.now()
    const resultId = `disc_${Date.now()}_${discoveryCounter}`
    const errors: DiscoveryError[] = []
    const allRawJobs: { provider: ProviderId; jobs: import('./types').RawJob[] }[] = []

    const providers = options?.providers
      ? providerRegistry.getAll().filter(p => options.providers!.includes(p.id))
      : providerRegistry.getPrioritized()

    const searchPromises = providers.map(async (provider) => {
      try {
        const searchStart = Date.now()
        const result = await provider.search(params)
        const latency = Date.now() - searchStart
        if (result.error) {
          providerHealthService.recordFailure(provider.id, result.error, latency)
          errors.push({ provider: provider.id, message: result.error, code: 'SEARCH_ERROR' })
        } else {
          providerHealthService.recordSuccess(provider.id, latency)
          if (result.jobs.length > 0) {
            allRawJobs.push({ provider: provider.id, jobs: result.jobs })
          }
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error'
        providerHealthService.recordFailure(provider.id, message)
        errors.push({ provider: provider.id, message, code: 'PROVIDER_ERROR' })
      }
    })

    await Promise.allSettled(searchPromises)

    const normalizedJobs: Job[] = []
    for (const { provider, jobs } of allRawJobs) {
      const sourceUrl = `https://${provider}.com/search?q=${encodeURIComponent(params.keywords)}`
      normalizedJobs.push(...normalizeJobs(jobs, provider, sourceUrl))
    }

    const { unique, duplicates } = deduplicate(normalizedJobs)

    const completedAt = new Date().toISOString()
    const executionTime = Date.now() - start
    const status = errors.length === 0 ? 'completed' : errors.length >= providers.length ? 'failed' : 'partial'

    const result: DiscoveryResult = {
      id: resultId,
      query: params.keywords,
      location: params.location,
      timestamp: start.toString(),
      providersUsed: providers.map(p => p.id),
      jobsFound: normalizedJobs.length,
      duplicatesRemoved: duplicates.length,
      uniqueJobs: unique.length,
      jobs: unique,
      errors,
      executionTime,
      completedAt,
      status: status as DiscoveryResult['status'],
    }

    result.timestamp = new Date(start).toISOString()

    discoveryHistoryService.add({
      id: result.id,
      query: result.query,
      location: result.location,
      timestamp: result.timestamp,
      providersUsed: result.providersUsed,
      jobsFound: result.jobsFound,
      duplicatesRemoved: result.duplicatesRemoved,
      uniqueJobs: result.uniqueJobs,
      errors: result.errors,
      executionTime: result.executionTime,
      status: result.status === 'running' ? 'completed' : result.status,
      profileId: options?.profileId ?? null,
    })

    return result
  },

  async searchProfile(profileId: string): Promise<DiscoveryResult> {
    const { searchProfileService } = await import('./search-profile')
    const profile = searchProfileService.get(profileId)
    if (!profile) throw new Error(`Search profile not found: ${profileId}`)

    const result = await this.search(
      {
        keywords: profile.keywords,
        location: profile.location,
        remote: profile.remote,
        salaryMin: profile.salaryMin,
        salaryMax: profile.salaryMax,
        experienceLevel: profile.experienceLevel,
        employmentType: profile.employmentType,
        postedWithinDays: null,
        easyApplyOnly: false,
        page: 1,
        pageSize: 50,
      },
      { providers: profile.enabledProviders, profileId }
    )

    searchProfileService.markRun(profileId)
    return result
  },
}
