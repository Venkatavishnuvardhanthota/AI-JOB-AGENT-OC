import type { SalaryMatchDetail } from './types'
import type { CandidateProfile } from './types'
import type { Job } from '@/services/discovery/types'

export function computeSalaryMatch(job: Job, profile: CandidateProfile): SalaryMatchDetail {
  const jobMin = job.salaryMin
  const jobMax = job.salaryMax
  const userMin = profile.salaryExpectationMin
  const userMax = profile.salaryExpectationMax

  const jobCurrency = job.currency
  const userCurrency = profile.salaryCurrency

  const normalizedJobMin = jobMin !== null && jobCurrency !== userCurrency ? convertCurrency(jobMin, jobCurrency, userCurrency) : jobMin
  const normalizedJobMax = jobMax !== null && jobCurrency !== userCurrency ? convertCurrency(jobMax, jobCurrency, userCurrency) : jobMax

  let marketAlignment: SalaryMatchDetail['marketAlignment'] = 'unknown'
  let score = 0.5

  if (normalizedJobMin !== null && normalizedJobMax !== null && userMin !== null && userMax !== null) {
    const userMid = (userMin + userMax) / 2
    const jobMid = (normalizedJobMin + normalizedJobMax) / 2
    if (jobMid < userMid * 0.85) {
      marketAlignment = 'below'
      score = 0.3
    } else if (jobMid <= userMax * 1.15) {
      marketAlignment = 'within'
      score = 1.0
    } else {
      marketAlignment = 'above'
      score = 0.8
    }
  } else if (normalizedJobMin !== null && normalizedJobMax !== null && userMin !== null) {
    if (normalizedJobMax < userMin) {
      marketAlignment = 'below'
      score = 0.3
    } else {
      marketAlignment = 'within'
      score = 0.8
    }
  } else if (normalizedJobMin !== null && normalizedJobMax !== null && userMax !== null) {
    if (normalizedJobMin > userMax) {
      marketAlignment = 'above'
      score = 0.7
    } else {
      marketAlignment = 'within'
      score = 0.8
    }
  } else if (normalizedJobMin !== null || normalizedJobMax !== null) {
    score = 0.6
    marketAlignment = 'within'
  } else if (userMin !== null || userMax !== null) {
    score = 0.5
    marketAlignment = 'unknown'
  }

  return {
    jobMin,
    jobMax,
    userMin: profile.salaryExpectationMin,
    userMax: profile.salaryExpectationMax,
    currency: jobCurrency || userCurrency,
    marketAlignment,
    score: Math.round(score * 100) / 100,
  }
}

function convertCurrency(amount: number, from: string | null, to: string | null): number {
  if (!from || !to || from === to) return amount
  const rates: Record<string, number> = {
    USD: 1, INR: 0.012, EUR: 1.08, GBP: 1.26, CAD: 0.73, AUD: 0.65, SGD: 0.74,
  }
  const fromRate = rates[from] ?? 1
  const toRate = rates[to] ?? 1
  return amount * (fromRate / toRate)
}
