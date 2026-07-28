import type { CandidateProfile, CandidateSkill, CandidateExperience, CandidateEducation } from './types'

export function buildCandidateProfile(profile: {
  headline?: string | null
  bio?: string | null
  location?: string | null
  salaryExpectationMin?: number | null
  salaryExpectationMax?: number | null
  salaryCurrency?: string | null
  portfolioUrl?: string | null
  linkedinUrl?: string | null
  githubUrl?: string | null
  skills?: { name: string; category?: string | null; proficiency?: number | null }[]
  experience?: { title: string; company: string; location?: string | null; startDate?: string | null; endDate?: string | null; isCurrent?: boolean; description?: string | null }[]
  education?: { institution: string; degree: string; fieldOfStudy?: string | null; startDate?: string | null; endDate?: string | null; gpa?: number | null }[]
  certifications?: { name: string; issuer?: string | null }[]
  languages?: { name: string; proficiency?: string }[]
  projects?: { name: string; description?: string | null; url?: string | null }[]
  visaSponsorshipRequired?: boolean
  remotePreference?: string | null
  preferredLocations?: string[]
  employmentType?: string | null
  preferredRoles?: string[]
}): CandidateProfile {
  const skills: CandidateSkill[] = (profile.skills || []).map(s => ({
    name: s.name,
    category: s.category ?? null,
    proficiency: s.proficiency ?? null,
  }))

  const experience: CandidateExperience[] = (profile.experience || []).map(e => ({
    title: e.title,
    company: e.company,
    location: e.location ?? null,
    startDate: e.startDate ?? null,
    endDate: e.endDate ?? null,
    isCurrent: e.isCurrent ?? false,
    description: e.description ?? null,
  }))

  const totalYearsOfExperience = computeTotalYears(experience)

  const education: CandidateEducation[] = (profile.education || []).map(e => ({
    institution: e.institution,
    degree: e.degree,
    fieldOfStudy: e.fieldOfStudy ?? null,
    startDate: e.startDate ?? null,
    endDate: e.endDate ?? null,
    gpa: e.gpa ?? null,
  }))

  return {
    preferredRoles: profile.preferredRoles || [],
    headline: profile.headline ?? null,
    bio: profile.bio ?? null,
    location: profile.location ?? null,
    salaryExpectationMin: profile.salaryExpectationMin ?? null,
    salaryExpectationMax: profile.salaryExpectationMax ?? null,
    salaryCurrency: profile.salaryCurrency ?? null,
    portfolioUrl: profile.portfolioUrl ?? null,
    linkedinUrl: profile.linkedinUrl ?? null,
    githubUrl: profile.githubUrl ?? null,
    skills,
    experience,
    education,
    certifications: (profile.certifications || []).map(c => ({ name: c.name, issuer: c.issuer ?? null })),
    languages: (profile.languages || []).map(l => ({ name: l.name, proficiency: l.proficiency ?? 'basic' })),
    projects: (profile.projects || []).map(p => ({ name: p.name, description: p.description ?? null, url: p.url ?? null })),
    visaSponsorshipRequired: profile.visaSponsorshipRequired ?? false,
    remotePreference: profile.remotePreference ?? null,
    preferredLocations: profile.preferredLocations || [],
    employmentType: profile.employmentType ?? null,
    totalYearsOfExperience,
  }
}

function computeTotalYears(experience: CandidateExperience[]): number {
  let totalMs = 0
  for (const exp of experience) {
    const start = exp.startDate ? new Date(exp.startDate).getTime() : null
    const end = exp.isCurrent ? Date.now() : exp.endDate ? new Date(exp.endDate).getTime() : null
    if (start && end) totalMs += end - start
  }
  return Math.round(totalMs / 31557600000 * 10) / 10
}

export function createDefaultProfile(): CandidateProfile {
  return {
    preferredRoles: [],
    headline: null,
    bio: null,
    location: null,
    salaryExpectationMin: null,
    salaryExpectationMax: null,
    salaryCurrency: null,
    portfolioUrl: null,
    linkedinUrl: null,
    githubUrl: null,
    skills: [],
    experience: [],
    education: [],
    certifications: [],
    languages: [],
    projects: [],
    visaSponsorshipRequired: false,
    remotePreference: null,
    preferredLocations: [],
    employmentType: null,
    totalYearsOfExperience: 0,
  }
}
