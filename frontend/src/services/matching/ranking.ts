import type { MatchResult, RankingCriteria } from './types'

export function rankJobs(matches: MatchResult[], criteria: RankingCriteria): MatchResult[] {
  const sorted = [...matches]
  const dir = criteria.direction === 'desc' ? -1 : 1

  switch (criteria.field) {
    case 'match':
      sorted.sort((a, b) => dir * (a.overall - b.overall))
      break
    case 'date':
      sorted.sort((a, b) => dir * (new Date(a.job.postedDate || a.job.discoveredAt).getTime() - new Date(b.job.postedDate || b.job.discoveredAt).getTime()))
      break
    case 'salary':
      sorted.sort((a, b) => dir * ((a.job.salaryMax || a.job.salaryMin || 0) - (b.job.salaryMax || b.job.salaryMin || 0)))
      break
    case 'experience':
      sorted.sort((a, b) => dir * (a.experienceDetail.userYears - b.experienceDetail.userYears))
      break
    case 'company':
      sorted.sort((a, b) => a.job.company.localeCompare(b.job.company))
      if (dir === 1) sorted.reverse()
      break
  }

  return sorted
}

export function rankByMatch(matches: MatchResult[]): MatchResult[] {
  return rankJobs(matches, { field: 'match', direction: 'desc' })
}

export function rankByNewest(matches: MatchResult[]): MatchResult[] {
  return rankJobs(matches, { field: 'date', direction: 'desc' })
}

export function rankBySalary(matches: MatchResult[]): MatchResult[] {
  return rankJobs(matches, { field: 'salary', direction: 'desc' })
}

export function rankByExperience(matches: MatchResult[]): MatchResult[] {
  return rankJobs(matches, { field: 'experience', direction: 'desc' })
}

export function rankByCompany(matches: MatchResult[]): MatchResult[] {
  return rankJobs(matches, { field: 'company', direction: 'asc' })
}
