import type { DetectedField, DocumentSelection } from './types'

export const documentSelector = {
  selectDocuments(
    fields: DetectedField[],
    availableResumes: string[],
    availableCoverLetters: string[],
    availablePortfolios: string[],
    availableCertificates: string[]
  ): DocumentSelection[] {
    const selections: DocumentSelection[] = []

    const resumeFields = fields.filter(f => this.isResumeField(f))
    const coverLetterFields = fields.filter(f => this.isCoverLetterField(f))
    const portfolioFields = fields.filter(f => this.isPortfolioField(f))
    const certificateFields = fields.filter(f => this.isCertificateField(f))

    if (resumeFields.length > 0) {
      selections.push({
        type: 'resume',
        name: availableResumes[0] ?? 'Resume',
        filePath: null,
        fileData: null,
        mimeType: 'application/pdf',
        required: resumeFields.some(f => f.required),
        selected: availableResumes.length > 0,
      })
    }

    if (coverLetterFields.length > 0 && availableCoverLetters.length > 0) {
      selections.push({
        type: 'cover_letter',
        name: availableCoverLetters[0] ?? 'Cover Letter',
        filePath: null,
        fileData: null,
        mimeType: 'application/pdf',
        required: coverLetterFields.some(f => f.required),
        selected: true,
      })
    }

    if (portfolioFields.length > 0 && availablePortfolios.length > 0) {
      selections.push({
        type: 'portfolio',
        name: availablePortfolios[0] ?? 'Portfolio',
        filePath: null,
        fileData: null,
        mimeType: 'application/pdf',
        required: portfolioFields.some(f => f.required),
        selected: true,
      })
    }

    if (certificateFields.length > 0 && availableCertificates.length > 0) {
      selections.push({
        type: 'certificate',
        name: availableCertificates[0] ?? 'Certificate',
        filePath: null,
        fileData: null,
        mimeType: 'application/pdf',
        required: certificateFields.some(f => f.required),
        selected: true,
      })
    }

    return selections
  },

  isResumeField(field: DetectedField): boolean {
    const label = (field.label ?? '').toLowerCase()
    const name = (field.name ?? '').toLowerCase()
    const placeholder = (field.placeholder ?? '').toLowerCase()
    const fieldType = field.fieldType
    return (
      fieldType === 'file' &&
      (label.includes('resume') || label.includes('cv') || label.includes('résumé') ||
       name.includes('resume') || name.includes('cv') ||
       placeholder.includes('resume') || placeholder.includes('cv'))
    )
  },

  isCoverLetterField(field: DetectedField): boolean {
    const label = (field.label ?? '').toLowerCase()
    const name = (field.name ?? '').toLowerCase()
    const placeholder = (field.placeholder ?? '').toLowerCase()
    return (
      (field.fieldType === 'file' || field.fieldType === 'textarea') &&
      (label.includes('cover letter') || name.includes('cover_letter') ||
       placeholder.includes('cover letter'))
    )
  },

  isPortfolioField(field: DetectedField): boolean {
    const label = (field.label ?? '').toLowerCase()
    const name = (field.name ?? '').toLowerCase()
    return (
      field.fieldType === 'file' &&
      (label.includes('portfolio') || name.includes('portfolio'))
    )
  },

  isCertificateField(field: DetectedField): boolean {
    const label = (field.label ?? '').toLowerCase()
    const name = (field.name ?? '').toLowerCase()
    return (
      field.fieldType === 'file' &&
      (label.includes('certificate') || label.includes('certification') ||
       name.includes('certificate') || name.includes('certification'))
    )
  },

  getRequiredDocumentTypes(selections: DocumentSelection[]): string[] {
    return selections.filter(s => s.required && !s.selected).map(s => s.type)
  },
}
