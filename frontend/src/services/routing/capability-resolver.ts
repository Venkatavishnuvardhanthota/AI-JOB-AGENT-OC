import type { ProviderId, ProviderCapability, SearchParams } from '../discovery/types'
import { providerRegistry } from '../discovery/provider-registry'
import { providerMetadataService } from './provider-metadata'

export const capabilityResolver = {
  resolveBySearchParams(params: SearchParams): ProviderId[] {
    const required: ProviderCapability[] = ['search']

    if (params.location) {
      required.push('filter_by_location')
    }
    if (params.salaryMin !== null || params.salaryMax !== null) {
      required.push('filter_by_salary')
    }
    if (params.experienceLevel) {
      required.push('filter_by_experience')
    }
    if (params.employmentType) {
      required.push('filter_by_type')
    }
    if (params.easyApplyOnly) {
      required.push('easy_apply')
    }

    const providers = providerRegistry.getEnabled()
    return providers
      .filter(p => required.every(c => p.capabilities.includes(c)))
      .map(p => p.id)
  },

  resolveByJobType(params: SearchParams): ProviderId[] {
    const providers = providerRegistry.getEnabled()
    const expLevel = params.experienceLevel
    const empType = params.employmentType

    return providers.filter(p => {
      const meta = providerMetadataService.get(p.id)
      if (empType === 'internship' && !meta.supportsInternships) return false
      if (expLevel === 'entry' || expLevel === 'internship') {
        if (!meta.supportsFreshers && !meta.supportsInternships) return false
      }
      return true
    }).map(p => p.id)
  },

  resolveForRemote(params: SearchParams): ProviderId[] {
    if (!params.remote || params.remote === 'any') {
      return providerRegistry.getEnabled().map(p => p.id)
    }
    if (params.remote === 'remote') {
      return providerRegistry.getEnabled()
        .filter(p => providerMetadataService.get(p.id).supportsRemote)
        .map(p => p.id)
    }
    return providerRegistry.getEnabled().map(p => p.id)
  },

  resolve(params: SearchParams): ProviderId[] {
    const byCaps = new Set(this.resolveBySearchParams(params))
    const byJobType = new Set(this.resolveByJobType(params))
    const byRemote = new Set(this.resolveForRemote(params))

    const allEnabled = providerRegistry.getEnabled().map(p => p.id)

    return allEnabled.filter(id =>
      byCaps.has(id) && byJobType.has(id) && byRemote.has(id)
    )
  },
}
