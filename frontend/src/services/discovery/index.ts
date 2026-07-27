export type {
  Job, RawJob, JobProvider, SearchParams, SearchResult,
  ProviderConfig, ProviderHealth, ProviderId, ProviderStatus, ProviderCapability,
  EmploymentType, ExperienceLevel, RemotePreference, ScheduleFrequency,
  DuplicateGroup, DuplicateMatchType,
  DiscoveryResult, DiscoveryError, DiscoveryHistoryEntry, DiscoveryStatistics, DiscoveryFilters, SearchProfile,
} from './types'

export { providerRegistry } from './provider-registry'
export { discoveryService } from './discovery'
export { normalizeJob, normalizeJobs, normalizeTitle, normalizeCompany, computeFreshness } from './normalization'
export { deduplicate, countDuplicates } from './deduplication'
export { discoveryHistoryService } from './discovery-history'
export { providerHealthService } from './provider-health'
export { searchProfileService } from './search-profile'
export { applyFilters, extractFilterOptions } from './filters'
