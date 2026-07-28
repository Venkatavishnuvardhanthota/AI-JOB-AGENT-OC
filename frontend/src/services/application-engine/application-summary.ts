import type { DetectedField, SemanticFieldMapping, FieldValidation, AIAnswer, DocumentSelection, ApplicationSummary, ApplicationSummaryField, MultiStepState } from './types'
import type { ProviderId } from '../discovery/types'

export const applicationSummaryBuilder = {
  build(
    providerId: ProviderId,
    jobTitle: string,
    companyName: string,
    fields: DetectedField[],
    mappings: Map<string, SemanticFieldMapping>,
    values: Record<string, string>,
    aiAnswers: AIAnswer[],
    documents: DocumentSelection[],
    validations: FieldValidation[],
    multiStep: MultiStepState
  ): ApplicationSummary {
    const summaryFields: ApplicationSummaryField[] = fields
      .filter(f => !f.disabled && f.fieldType !== 'hidden' && f.fieldType !== 'submit')
      .map(field => {
        const mapping = mappings.get(field.id)
        const value = values[field.id]
        const validation = validations.find(v => v.fieldId === field.id)
        const aiAnswer = (field.fieldType === 'textarea' || field.fieldType === 'text')
          ? aiAnswers.find(a => a.answer === value)
          : undefined

        let source: ApplicationSummaryField['source'] = 'empty'
        if (value && mapping && mapping.profilePath) source = 'profile'
        else if (value && aiAnswer) source = 'ai'
        else if (value && field.fieldType === 'file') source = 'document'
        else if (value && !mapping) source = 'manual'
        else if (value) source = 'manual'

        return {
          fieldName: field.label ?? field.name ?? field.id,
          category: mapping?.category ?? 'custom',
          value: value ?? null,
          mapped: mapping !== undefined && mapping.confidence >= 0.3,
          validated: !validation || validation.severity !== 'error',
          source,
        }
      })

    const aiGenerated = aiAnswers.filter(a => a.generated).length
    const docsSelected = documents.filter(d => d.selected).length
    const errors = validations.filter(v => v.severity === 'error').length
    const warnings = validations.filter(v => v.severity === 'warning').length
    const ready = errors === 0 && docsSelected >= documents.filter(d => d.required).length

    return {
      providerId,
      jobTitle,
      companyName,
      fields: summaryFields,
      aiAnswers: aiGenerated,
      documentsSelected: docsSelected,
      validationErrors: errors,
      validationWarnings: warnings,
      totalSteps: multiStep.totalSteps,
      currentStep: multiStep.currentStep,
      ready,
    }
  },

  isReady(summary: ApplicationSummary): boolean {
    return summary.ready
  },

  getReadinessIssues(summary: ApplicationSummary): string[] {
    const issues: string[] = []

    if (summary.validationErrors > 0) {
      issues.push(`${summary.validationErrors} validation error(s) need to be fixed`)
    }

    const emptyRequired = summary.fields.filter(f => !f.value && f.mapped)
    if (emptyRequired.length > 0) {
      issues.push(`${emptyRequired.length} mapped field(s) have no value`)
    }

    const invalidFields = summary.fields.filter(f => !f.validated)
    if (invalidFields.length > 0) {
      issues.push(`${invalidFields.length} field(s) failed validation`)
    }

    return issues
  },
}
