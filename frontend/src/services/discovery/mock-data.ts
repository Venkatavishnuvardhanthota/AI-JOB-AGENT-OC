import type { SearchParams, RawJob, ProviderId } from './types'

const LOCATIONS = ['San Francisco, CA', 'New York, NY', 'Seattle, WA', 'Austin, TX', 'Remote']
const SKILLS = ['TypeScript', 'React', 'Node.js', 'Python', 'Go', 'AWS', 'Docker', 'Kubernetes']
const COMMON_RESPONSIBILITIES = ['Design and implement new features', 'Write clean, maintainable code', 'Participate in code reviews', 'Mentor junior engineers']
const COMMON_BENEFITS = ['Health insurance', '401(k) matching', 'Unlimited PTO', 'Remote work options']

export function generateMockJobs(
  params: SearchParams,
  providerId: ProviderId,
  companies: string[],
  count: number,
  titleSuffix: string,
  baseSalaryMin: number,
  baseSalaryMax: number,
  opts?: {
    alwaysEasyApply?: boolean
    visaMod?: number
    locationPool?: string[]
    remoteMod?: number
    expLevels?: string[]
  }
): RawJob[] {
  const actualCount = Math.min(params.pageSize, count)
  const jobs: RawJob[] = []
  const locs = opts?.locationPool ?? LOCATIONS

  for (let i = 0; i < actualCount; i++) {
    const company = companies[(params.page * actualCount + i) % companies.length]
    const remoteVal = opts?.remoteMod !== undefined
      ? (i % opts.remoteMod === 0 ? 'Remote' : 'On-site')
      : i % 3 === 0 ? 'Remote' : i % 3 === 1 ? 'Hybrid' : 'On-site'

    jobs.push({
      externalId: `${providerId}_${Date.now()}_${i}`,
      title: params.keywords ? `${params.keywords} ${titleSuffix}` : `Software ${titleSuffix}`,
      company,
      companyLogo: null,
      companyWebsite: `https://${company.toLowerCase().replace(/\s+/g, '')}.com`,
      location: locs[i % locs.length],
      remote: remoteVal,
      employmentType: 'Full-time',
      experienceLevel: opts?.expLevels ? opts.expLevels[i % opts.expLevels.length] : i % 2 === 0 ? 'Mid-Senior' : 'Associate',
      salaryMin: baseSalaryMin + i * 25000,
      salaryMax: baseSalaryMax + i * 30000,
      currency: 'USD',
      description: `Join ${company} as a ${params.keywords || 'Software'} ${titleSuffix}. You will build and maintain scalable systems.`,
      responsibilities: COMMON_RESPONSIBILITIES,
      requiredSkills: SKILLS.slice(0, 4),
      preferredSkills: SKILLS.slice(4, 7),
      benefits: COMMON_BENEFITS,
      visaSponsorship: opts?.visaMod !== undefined ? i % opts.visaMod !== 0 : i % 3 !== 0,
      postedDate: new Date(Date.now() - i * 86400000).toISOString(),
      applicationDeadline: null,
      easyApply: opts?.alwaysEasyApply ?? i % 2 === 0,
      tags: [params.keywords || 'software', 'engineering', company.toLowerCase()],
      metadata: { country: 'US', industry: 'Technology', companySize: '10000+' },
    })
  }
  return jobs
}
