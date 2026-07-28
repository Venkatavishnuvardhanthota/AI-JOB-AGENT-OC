import type { DetectedField, SemanticFieldCategory, SemanticFieldMapping } from './types'

interface MappingRule {
  patterns: RegExp[]
  category: SemanticFieldCategory
  profilePath: string | null
}

const MAPPING_RULES: MappingRule[] = [
  { patterns: [/^first(_|\s|-)?name$/i, /^fname$/i, /^given[_]?name$/i], category: 'first_name', profilePath: 'firstName' },
  { patterns: [/^last(_|\s|-)?name$/i, /^lname$/i, /^surname$/i, /^family[_]?name$/i], category: 'last_name', profilePath: 'lastName' },
  { patterns: [/^full[_]?name$/i, /^your[_]?name$/i, /^candidate[_]?name$/i, /^applicant[_]?name$/i], category: 'full_name', profilePath: null },
  { patterns: [/^email/i, /^e[\s-]?mail$/i, /^email[_]?address$/i], category: 'email', profilePath: 'email' },
  { patterns: [/^phone$/i, /^telephone$/i, /^mobile$/i, /^cell$/i, /^contact[_]?(number|phone)?$/i, /^phone[_]?number$/i], category: 'phone', profilePath: 'phone' },
  { patterns: [/^current[_]?company$/i, /^company$/i, /^employer$/i], category: 'current_company', profilePath: 'currentCompany' },
  { patterns: [/^current[_]?(role|title|position)$/i, /^job[_]?(title|role)$/i, /^title$/i, /^position$/i], category: 'current_role', profilePath: 'currentRole' },
  { patterns: [/^years[_]?(of)?[_]?experience$/i, /^experience$/i, /^total[_]?experience$/i], category: 'years_experience', profilePath: 'yearsOfExperience' },
  { patterns: [/^expected[_]?salary$/i, /^desired[_]?salary$/i, /^salary[_]?(expectation|requirement)?$/i], category: 'expected_salary', profilePath: 'expectedSalary' },
  { patterns: [/^current[_]?salary$/i], category: 'current_salary', profilePath: 'currentSalary' },
  { patterns: [/^notice[_]?(period|time)?$/i, /^notice$/i], category: 'notice_period', profilePath: 'noticePeriod' },
  { patterns: [/^location$/i, /^current[_]?location$/i], category: 'location', profilePath: 'location' },
  { patterns: [/^address$/i, /^street[_]?address$/i], category: 'address', profilePath: null },
  { patterns: [/^country$/i], category: 'country', profilePath: null },
  { patterns: [/^state$/i, /^province$/i, /^region$/i], category: 'state', profilePath: null },
  { patterns: [/^city$/i, /^town$/i], category: 'city', profilePath: null },
  { patterns: [/^zip[_]?(code|postal)?$/i, /^postal[_]?(code|zip)?$/i], category: 'zip_code', profilePath: null },
  { patterns: [/^university$/i, /^college$/i, /^school$/i, /^institution$/i, /^educational[_]?institution$/i], category: 'university', profilePath: null },
  { patterns: [/^degree$/i, /^qualification$/i], category: 'degree', profilePath: null },
  { patterns: [/^graduation[_]?year$/i, /^year[_]?(of)?[_]?(graduation|passing)$/i], category: 'graduation_year', profilePath: null },
  { patterns: [/^portfolio[_]?(url|link)?$/i, /^portfolio$/i], category: 'portfolio', profilePath: 'portfolioUrl' },
  { patterns: [/^github[_]?(url|link|profile)?$/i, /^github$/i], category: 'github', profilePath: 'githubUrl' },
  { patterns: [/^linkedin[_]?(url|link|profile)?$/i, /^linkedin/i], category: 'linkedin', profilePath: 'linkedinUrl' },
  { patterns: [/^website$/i, /^web[_]?site$/i, /^personal[_]?(website|url|site)?$/i], category: 'website', profilePath: 'website' },
  { patterns: [/^visa[_]?(status|type)?$/i, /^work[_]?visa$/i], category: 'visa_status', profilePath: 'visaStatus' },
  { patterns: [/^work[_]?(authorization|eligibility|permit)?$/i, /^authorization$/i], category: 'work_authorization', profilePath: 'workAuthorization' },
  { patterns: [/^cover[_]?letter$/i], category: 'cover_letter', profilePath: null },
  { patterns: [/^resume$/i, /^cv$/i], category: 'resume', profilePath: null },
  { patterns: [/^headline$/i, /^professional[_]?(headline|title)?$/i], category: 'headline', profilePath: 'headline' },
  { patterns: [/^bio$/i, /^about$/i, /^summary$/i, /^professional[_]?summary$/i], category: 'bio', profilePath: 'bio' },
  { patterns: [/^skills$/i, /^technologies$/i], category: 'skills', profilePath: null },
  { patterns: [/^certification/i, /^certificate/i], category: 'certification', profilePath: null },
  { patterns: [/^language/i], category: 'language', profilePath: null },
  { patterns: [/^start[_]?date$/i], category: 'start_date', profilePath: null },
  { patterns: [/^end[_]?date$/i], category: 'end_date', profilePath: null },
  { patterns: [/^how[_]?(did|do)[_]?(you|they)?[_]?hear/i, /^referral[_]?source$/i, /^source$/i], category: 'how_did_you_hear', profilePath: null },
  { patterns: [/^gender$/i], category: 'gender', profilePath: null },
  { patterns: [/^ethnicity$/i, /^race$/i], category: 'ethnicity', profilePath: null },
  { patterns: [/^veteran/i], category: 'veteran_status', profilePath: null },
  { patterns: [/^disability/i], category: 'disability_status', profilePath: null },
  { patterns: [/^salary[_]?min/i, /^minimum[_]?salary/i], category: 'salary_min', profilePath: 'salaryMin' },
  { patterns: [/^salary[_]?max/i, /^maximum[_]?salary/i], category: 'salary_max', profilePath: 'salaryMax' },
  { patterns: [/^currency$/i, /^salary[_]?currency$/i], category: 'salary_currency', profilePath: 'salaryCurrency' },
]

function normalizeText(text: string): string {
  return text
    .replace(/[^a-z0-9\s_-]/gi, ' ')
    .replace(/[-_]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function scoreMatch(field: DetectedField, rule: MappingRule): number {
  const sources = [
    field.label ? normalizeText(field.label) : '',
    field.placeholder ? normalizeText(field.placeholder) : '',
    field.name ? normalizeText(field.name) : '',
  ].filter(Boolean)

  let maxScore = 0
  for (const source of sources) {
    for (const pattern of rule.patterns) {
      if (pattern.test(source)) {
        const matchLen = source.match(pattern)?.[0]?.length ?? 0
        const exactness = matchLen / Math.max(source.length, 1)
        maxScore = Math.max(maxScore, exactness)
      }
    }
  }
  return maxScore
}

export const semanticFieldMapper = {
  mapFields(fields: DetectedField[]): SemanticFieldMapping[] {
    return fields.map(field => {
      let bestCategory: SemanticFieldCategory = 'custom'
      let bestConfidence = 0
      let bestProfilePath: string | null = null

      for (const rule of MAPPING_RULES) {
        const score = scoreMatch(field, rule)
        if (score > bestConfidence) {
          bestConfidence = score
          bestCategory = rule.category
          bestProfilePath = rule.profilePath
        }
      }

      return {
        fieldId: field.id,
        category: bestCategory,
        confidence: bestConfidence,
        profilePath: bestProfilePath,
        defaultValue: field.value,
      }
    })
  },

  getMappingForField(field: DetectedField): SemanticFieldMapping {
    const mappings = this.mapFields([field])
    return mappings[0]
  },

  getUnmappedFields(mappings: SemanticFieldMapping[]): SemanticFieldMapping[] {
    return mappings.filter(m => m.confidence < 0.3)
  },
}
