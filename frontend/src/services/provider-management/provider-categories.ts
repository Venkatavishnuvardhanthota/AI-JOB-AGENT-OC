import type { ProviderMetadata } from '../routing/routing-types'
import type { ManagedProvider, ProviderCategory } from './provider-management-types'

export function categorizeProvider(metadata: ProviderMetadata): string {
  if (metadata.featureSupport.includes('ats_integration')) return 'ATS Providers'
  if (metadata.featureSupport.includes('startup_focus') || metadata.featureSupport.includes('yc_alumni')) return 'Startup Platforms'
  if (metadata.region.includes('india') && metadata.country.length === 1 && metadata.country[0] === 'in') {
    if (metadata.supportsInternships && metadata.jobTypes.includes('internship')) return 'Indian Job Portals'
    return 'Indian Job Portals'
  }
  if (metadata.region.includes('global') && metadata.country.length > 4) return 'Global Job Boards'
  if (metadata.supportsRemote && metadata.featureSupport.includes('direct_apply')) return 'Remote Job Boards'
  return 'Future Providers'
}

export function getCategories(providers: ManagedProvider[]): ProviderCategory[] {
  const grouped = new Map<string, ManagedProvider[]>()

  for (const p of providers) {
    const category = p.category
    if (!grouped.has(category)) {
      grouped.set(category, [])
    }
    grouped.get(category)!.push(p)
  }

  return Array.from(grouped.entries())
    .map(([name, providers]) => ({
      name,
      providers,
      count: providers.length,
    }))
    .sort((a, b) => b.count - a.count)
}

export function getAllCategoryNames(providers: ManagedProvider[]): string[] {
  const names = new Set(providers.map(p => p.category))
  return Array.from(names).sort()
}
