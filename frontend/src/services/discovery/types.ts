export type EmploymentType = 'full_time' | 'part_time' | 'contract' | 'internship' | 'temporary' | 'volunteer' | 'freelance'
export type ExperienceLevel = 'internship' | 'entry' | 'associate' | 'mid_senior' | 'director' | 'executive'
export type RemotePreference = 'remote' | 'hybrid' | 'onsite' | 'any'
export type ProviderId = 'linkedin' | 'indeed' | 'naukri' | 'foundit' | 'wellfound' | 'ycombinator' | 'company_careers' | 'internshala' | 'unstop' | 'freshersworld' | 'greenhouse' | 'lever' | 'ashby' | 'smartrecruiters'
export type ScheduleFrequency = 'manual' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'custom_cron'
export type ProviderCapability = 'search' | 'filter_by_location' | 'filter_by_salary' | 'filter_by_experience' | 'filter_by_type' | 'easy_apply' | 'company_profile' | 'salary_range'
export type ProviderStatus = 'healthy' | 'degraded' | 'unhealthy' | 'disabled'
export type DuplicateMatchType = 'exact' | 'high_confidence' | 'medium_confidence' | 'low_confidence'

export interface Job {
  id: string
  provider: ProviderId
  sourceUrl: string
  externalId: string
  title: string
  company: string
  companyLogo: string | null
  companyWebsite: string | null
  location: string
  country: string | null
  remote: RemotePreference
  employmentType: EmploymentType
  experienceLevel: ExperienceLevel | null
  salaryMin: number | null
  salaryMax: number | null
  currency: string | null
  description: string
  responsibilities: string[]
  requiredSkills: string[]
  preferredSkills: string[]
  benefits: string[]
  visaSponsorship: boolean | null
  postedDate: string | null
  applicationDeadline: string | null
  easyApply: boolean
  tags: string[]
  metadata: Record<string, unknown>
  normalizedTitle: string
  normalizedCompany: string
  freshnessScore: number
  discoveredAt: string
}

export interface JobProvider {
  id: ProviderId
  name: string
  enabled: boolean
  priority: number
  capabilities: ProviderCapability[]
  search(params: SearchParams): Promise<SearchResult>
  health(): Promise<ProviderHealth>
}

export interface SearchParams {
  keywords: string
  location: string | null
  remote: RemotePreference | null
  salaryMin: number | null
  salaryMax: number | null
  experienceLevel: ExperienceLevel | null
  employmentType: EmploymentType | null
  postedWithinDays: number | null
  easyApplyOnly: boolean
  page: number
  pageSize: number
}

export interface SearchResult {
  jobs: RawJob[]
  totalResults: number
  page: number
  pageSize: number
  hasMore: boolean
  provider: ProviderId
  duration: number
  error: string | null
}

export interface RawJob {
  externalId: string
  title: string
  company: string
  companyLogo: string | null
  companyWebsite: string | null
  location: string
  remote: string | null
  employmentType: string | null
  experienceLevel: string | null
  salaryMin: number | null
  salaryMax: number | null
  currency: string | null
  description: string
  responsibilities: string[]
  requiredSkills: string[]
  preferredSkills: string[]
  benefits: string[]
  visaSponsorship: boolean | null
  postedDate: string | null
  applicationDeadline: string | null
  easyApply: boolean
  tags: string[]
  metadata: Record<string, unknown>
}

export interface ProviderConfig {
  id: ProviderId
  name: string
  enabled: boolean
  priority: number
  capabilities: ProviderCapability[]
  baseUrl: string | null
  apiKeyRequired: boolean
  apiKeyConfigured: boolean
}

export interface ProviderHealth {
  status: ProviderStatus
  lastSuccess: string | null
  lastFailure: string | null
  successRate: number
  averageLatency: number
  errorCount: number
  availability: number
  consecutiveFailures: number
  lastError: string | null
}

export interface DuplicateGroup {
  masterJob: Job
  duplicates: Job[]
  matchType: DuplicateMatchType
  matchReasons: string[]
}

export interface DiscoveryResult {
  id: string
  query: string
  location: string | null
  timestamp: string
  providersUsed: ProviderId[]
  jobsFound: number
  duplicatesRemoved: number
  uniqueJobs: number
  jobs: Job[]
  errors: DiscoveryError[]
  executionTime: number
  completedAt: string | null
  status: 'running' | 'completed' | 'partial' | 'failed'
}

export interface DiscoveryError {
  provider: ProviderId
  message: string
  code: string
}

export interface SearchProfile {
  id: string
  name: string
  keywords: string
  location: string | null
  salaryMin: number | null
  salaryMax: number | null
  experienceLevel: ExperienceLevel | null
  employmentType: EmploymentType | null
  remote: RemotePreference | null
  enabledProviders: ProviderId[]
  scheduleFrequency: ScheduleFrequency
  createdAt: string
  updatedAt: string
  lastRunAt: string | null
}

export interface DiscoveryHistoryEntry {
  id: string
  query: string
  location: string | null
  timestamp: string
  providersUsed: ProviderId[]
  jobsFound: number
  duplicatesRemoved: number
  uniqueJobs: number
  errors: DiscoveryError[]
  executionTime: number
  status: 'completed' | 'partial' | 'failed'
  profileId: string | null
}

export interface DiscoveryStatistics {
  totalSearches: number
  totalJobsDiscovered: number
  totalDuplicatesRemoved: number
  averageExecutionTime: number
  searchesToday: number
  searchesThisWeek: number
  searchesThisMonth: number
  topKeywords: { keyword: string; count: number }[]
  topCompanies: { company: string; count: number }[]
  topLocations: { location: string; count: number }[]
}

export interface DiscoveryFilters {
  providers: ProviderId[]
  companies: string[]
  locations: string[]
  remote: RemotePreference | null
  salaryMin: number | null
  salaryMax: number | null
  experienceLevel: ExperienceLevel | null
  employmentType: EmploymentType | null
  skills: string[]
  postedWithinDays: number | null
  easyApplyOnly: boolean
  tags: string[]
}
