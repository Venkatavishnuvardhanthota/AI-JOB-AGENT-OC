import type { CapabilityId, ProviderCapabilityDescriptor } from './types'

const CAPABILITY_DESCRIPTIONS: Record<CapabilityId, ProviderCapabilityDescriptor> = {
  search: { id: 'search', name: 'Search', description: 'Can search for jobs' },
  apply: { id: 'apply', name: 'Apply', description: 'Can submit job applications' },
  authentication: { id: 'authentication', name: 'Authentication', description: 'Requires authentication' },
  browser_automation: { id: 'browser_automation', name: 'Browser Automation', description: 'Uses browser automation' },
  api: { id: 'api', name: 'API', description: 'Uses REST API' },
  resume_upload: { id: 'resume_upload', name: 'Resume Upload', description: 'Supports resume upload' },
  cover_letter_upload: { id: 'cover_letter_upload', name: 'Cover Letter Upload', description: 'Supports cover letter upload' },
  questionnaire: { id: 'questionnaire', name: 'Questionnaire', description: 'Handles application questionnaires' },
  tracking: { id: 'tracking', name: 'Tracking', description: 'Tracks application status' },
  salary_range: { id: 'salary_range', name: 'Salary Range', description: 'Provides salary information' },
  company_profile: { id: 'company_profile', name: 'Company Profile', description: 'Provides company details' },
  filter_by_location: { id: 'filter_by_location', name: 'Filter by Location', description: 'Supports location filtering' },
  filter_by_salary: { id: 'filter_by_salary', name: 'Filter by Salary', description: 'Supports salary filtering' },
  filter_by_experience: { id: 'filter_by_experience', name: 'Filter by Experience', description: 'Supports experience level filtering' },
  filter_by_type: { id: 'filter_by_type', name: 'Filter by Type', description: 'Supports employment type filtering' },
  easy_apply: { id: 'easy_apply', name: 'Easy Apply', description: 'Supports one-click applications' },
}

export const capabilitySystem = {
  getDescriptor(id: CapabilityId): ProviderCapabilityDescriptor {
    return CAPABILITY_DESCRIPTIONS[id]
  },

  getAllDescriptors(): ProviderCapabilityDescriptor[] {
    return Object.values(CAPABILITY_DESCRIPTIONS)
  },

  hasCapability(capabilities: CapabilityId[], id: CapabilityId): boolean {
    return capabilities.includes(id)
  },

  hasAllCapabilities(capabilities: CapabilityId[], required: CapabilityId[]): boolean {
    return required.every(c => this.hasCapability(capabilities, c))
  },

  hasAnyCapability(capabilities: CapabilityId[], required: CapabilityId[]): boolean {
    return required.some(c => this.hasCapability(capabilities, c))
  },

  getMissingCapabilities(capabilities: CapabilityId[], required: CapabilityId[]): CapabilityId[] {
    return required.filter(c => !this.hasCapability(capabilities, c))
  },

  mergeCapabilities(...capabilitySets: CapabilityId[][]): CapabilityId[] {
    const merged = new Set<CapabilityId>()
    for (const set of capabilitySets) {
      for (const cap of set) merged.add(cap)
    }
    return [...merged]
  },

  intersectCapabilities(...capabilitySets: CapabilityId[][]): CapabilityId[] {
    if (capabilitySets.length === 0) return []
    return capabilitySets[0].filter(cap =>
      capabilitySets.every(set => set.includes(cap))
    )
  },

  toDisplayNames(capabilities: CapabilityId[]): string[] {
    return capabilities.map(c => CAPABILITY_DESCRIPTIONS[c]?.name ?? c)
  },
}
