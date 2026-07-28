import type { DetectedField, SemanticFieldMapping, ProfileData, ProfileEducation, ProfileExperience, ProfileProject, ProfileCertification, ProfileLanguage } from './types'
import { semanticFieldMapper } from './semantic-field-mapper'
import { fieldDetector } from './field-detector'

function buildEmptyProfile(): ProfileData {
  return {
    firstName: '', lastName: '', email: '', phone: '', headline: '', bio: '',
    location: '', portfolioUrl: '', linkedinUrl: '', githubUrl: '', website: '',
    currentCompany: '', currentRole: '', yearsOfExperience: '', expectedSalary: '',
    currentSalary: '', salaryMin: '', salaryMax: '', salaryCurrency: '',
    noticePeriod: '', workAuthorization: '', visaStatus: '',
    education: [], experience: [], projects: [], skills: [],
    certifications: [], languages: [],
  }
}

function resolveNestedPath(obj: Record<string, unknown>, path: string): string {
  const parts = path.split('.')
  let current: unknown = obj
  for (const part of parts) {
    if (current === null || current === undefined) return ''
    if (typeof current !== 'object') return ''
    current = (current as Record<string, unknown>)[part]
  }
  return (current as string) ?? ''
}

function getProfilePathValue(profile: ProfileData, path: string | null): string | null {
  if (!path) return null
  const value = resolveNestedPath(profile as unknown as Record<string, unknown>, path)
  return value || null
}

export const profileMapper = {
  buildProfile(
    userProfile: Partial<ProfileData> = {},
    education: ProfileEducation[] = [],
    experience: ProfileExperience[] = [],
    projects: ProfileProject[] = [],
    skills: string[] = [],
    certifications: ProfileCertification[] = [],
    languages: ProfileLanguage[] = []
  ): ProfileData {
    return {
      ...buildEmptyProfile(),
      ...userProfile,
      education: education.length > 0 ? education : userProfile.education ?? [],
      experience: experience.length > 0 ? experience : userProfile.experience ?? [],
      projects: projects.length > 0 ? projects : userProfile.projects ?? [],
      skills: skills.length > 0 ? skills : userProfile.skills ?? [],
      certifications: certifications.length > 0 ? certifications : userProfile.certifications ?? [],
      languages: languages.length > 0 ? languages : userProfile.languages ?? [],
    }
  },

  mapFieldFromProfile(field: DetectedField, profile: ProfileData): { value: string | null; source: 'profile' | 'empty' } {
    const mapping = semanticFieldMapper.getMappingForField(field)

    if (mapping.profilePath && mapping.confidence >= 0.3) {
      const value = getProfilePathValue(profile, mapping.profilePath)
      if (value) return { value, source: 'profile' }
    }

    if (mapping.category === 'full_name' && profile.firstName) {
      const fullName = [profile.firstName, profile.lastName].filter(Boolean).join(' ')
      if (fullName) return { value: fullName, source: 'profile' }
    }

    if (mapping.category === 'skills' && profile.skills.length > 0) {
      return { value: profile.skills.slice(0, 10).join(', '), source: 'profile' }
    }

    return { value: null, source: 'empty' }
  },

  mapFieldsFromProfile(fields: DetectedField[], profile: ProfileData): { fieldId: string; value: string | null; source: 'profile' | 'empty' }[] {
    const fillable = fieldDetector.getFillableFields(fields)
    return fillable.map(field => ({
      fieldId: field.id,
      ...this.mapFieldFromProfile(field, profile),
    }))
  },

  getRequiredUnmappedFields(fields: DetectedField[], profile: ProfileData): { field: DetectedField; mapping: SemanticFieldMapping }[] {
    const fillable = fieldDetector.getFillableFields(fields)
    const result: { field: DetectedField; mapping: SemanticFieldMapping }[] = []

    for (const field of fillable) {
      if (!field.required) continue
      const mapping = semanticFieldMapper.getMappingForField(field)
      const { value } = this.mapFieldFromProfile(field, profile)
      if (!value && mapping.confidence >= 0.3) {
        result.push({ field, mapping })
      }
    }

    return result
  },

  getProfileCompleteness(profile: ProfileData): { filled: number; total: number; percentage: number } {
    const fields: string[] = [
      'firstName', 'lastName', 'email', 'phone', 'headline', 'bio',
      'location', 'portfolioUrl', 'linkedinUrl', 'githubUrl', 'website',
      'currentCompany', 'currentRole', 'yearsOfExperience',
      'expectedSalary', 'noticePeriod', 'workAuthorization',
    ]

    const filled = fields.filter(f => {
      const value = resolveNestedPath(profile as unknown as Record<string, unknown>, f)
      return value !== '' && value !== undefined
    }).length

    const sectionBonus =
      (profile.education.length > 0 ? 5 : 0) +
      (profile.experience.length > 0 ? 5 : 0) +
      (profile.skills.length > 0 ? 5 : 0) +
      (profile.certifications.length > 0 ? 3 : 0) +
      (profile.languages.length > 0 ? 2 : 0)

    const total = fields.length + 20
    const filledWithBonus = filled + sectionBonus

    return {
      filled: filledWithBonus,
      total,
      percentage: Math.round((filledWithBonus / total) * 100),
    }
  },
}
