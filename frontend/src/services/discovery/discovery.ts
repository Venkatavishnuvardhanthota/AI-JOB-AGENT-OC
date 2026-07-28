import type { DiscoveryResult, SearchParams, ProviderId } from './types'
import { providerRouter } from '../routing/provider-router'

let discoveryCounter = 0

export const discoveryService = {
  async search(
    params: SearchParams,
    options?: { providers?: ProviderId[]; profileId?: string }
  ): Promise<DiscoveryResult> {
    discoveryCounter++

    const policy = {
      enabled: true,
      enableHealthAware: true,
      enableFallback: true,
      enableDuplicateResolution: true,
    }

    const config = options?.providers ? {
      preferredProviders: options.providers,
    } : undefined

    const { discoveryResult } = await providerRouter.search(params, {
      ...options,
      policy,
      config: config ? { ...config, excludedProviders: [] } : undefined,
    })

    return discoveryResult
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
