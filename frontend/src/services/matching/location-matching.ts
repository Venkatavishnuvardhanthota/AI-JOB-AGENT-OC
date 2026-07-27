import type { LocationMatchDetail } from './types'
import type { CandidateProfile } from './types'
import type { Job } from '@/services/discovery/types'

export function computeLocationMatch(job: Job, profile: CandidateProfile): LocationMatchDetail {
  const remoteMatch = profile.remotePreference
    ? job.remote === profile.remotePreference || profile.remotePreference === 'any'
    : job.remote === 'remote'

  const locationMatch = profile.location
    ? normalizeLocation(job.location).includes(normalizeLocation(profile.location)) ||
      normalizeLocation(profile.location).includes(normalizeLocation(job.location))
    : true

  const relocationRequired = profile.location
    ? !locationMatch && job.remote !== 'remote'
    : false

  let score = 0
  if (job.remote === 'remote') {
    score = 1.0
  } else if (remoteMatch) {
    score = 0.9
  } else if (locationMatch) {
    score = 0.8
  } else if (relocationRequired) {
    score = 0.4
  } else {
    score = 0.5
  }

  return {
    remoteMatch,
    locationMatch,
    relocationRequired,
    remotePreference: profile.remotePreference,
    jobRemote: job.remote,
    score: Math.round(score * 100) / 100,
  }
}

function normalizeLocation(location: string): string {
  return location
    .toLowerCase()
    .replace(/[,;]\s*/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}
