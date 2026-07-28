import type { DetectedField, FieldValidation, SemanticFieldMapping } from './types'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const PHONE_RE = /^[\+]?[(]?[0-9]{1,4}[)]?[-\s./0-9]{6,15}$/
const URL_RE = /^https?:\/\/.+\..+/
const NUMBER_RE = /^-?\d+(\.\d+)?$/
export const validationEngine = {
  validateField(field: DetectedField, value: string, mapping: SemanticFieldMapping | null): FieldValidation | null {
    if (field.required && !value) {
      return this.createError(field, 'required', `${field.label ?? 'This field'} is required`)
    }

    if (!value) return null

    switch (field.fieldType) {
      case 'email': {
        if (!EMAIL_RE.test(value)) {
          return this.createError(field, 'format', 'Invalid email format')
        }
        break
      }
      case 'phone': {
        if (!PHONE_RE.test(value)) {
          return this.createWarning(field, 'format', 'Phone format may be invalid')
        }
        break
      }
      case 'url': {
        if (!URL_RE.test(value)) {
          return this.createError(field, 'format', 'Invalid URL format')
        }
        break
      }
      case 'number': {
        if (!NUMBER_RE.test(value)) {
          return this.createError(field, 'format', 'Must be a valid number')
        }
        break
      }
      case 'date': {
        if (isNaN(Date.parse(value))) {
          return this.createError(field, 'format', 'Invalid date format')
        }
        break
      }
    }

    if (field.fieldType === 'email' && mapping && mapping.category === 'email' && !EMAIL_RE.test(value)) {
      return this.createError(field, 'format', 'Please enter a valid email address')
    }

    if (field.fieldType === 'url' && URL_RE.test(value)) {
      return null
    }

    return null
  },

  validateFields(fields: DetectedField[], values: Record<string, string>, mappings: Map<string, SemanticFieldMapping>): FieldValidation[] {
    const errors: FieldValidation[] = []

    for (const field of fields) {
      if (field.disabled || field.readonly || field.fieldType === 'hidden' || field.fieldType === 'submit') continue

      const value = values[field.id] ?? ''
      const mapping = mappings.get(field.id) ?? null
      const validation = this.validateField(field, value, mapping)
      if (validation) errors.push(validation)
    }

    return errors
  },

  checkDuplicateValues(values: Record<string, string>): FieldValidation[] {
    const errors: FieldValidation[] = []
    const seen = new Map<string, string[]>()

    for (const [fieldId, value] of Object.entries(values)) {
      if (!value) continue
      const existing = seen.get(value)
      if (existing) {
        existing.push(fieldId)
      } else {
        seen.set(value, [fieldId])
      }
    }

    for (const [, fieldIds] of seen) {
      if (fieldIds.length > 1) {
        fieldIds.forEach(id => {
          errors.push({
            fieldId: id,
            fieldName: id,
            severity: 'warning',
            message: 'Duplicate value detected',
            category: 'duplicate',
          })
        })
      }
    }

    return errors
  },

  validateRequiredUploads(fields: DetectedField[], selections: { fieldId: string; selected: boolean }[]): FieldValidation[] {
    const errors: FieldValidation[] = []
    for (const field of fields) {
      if (field.fieldType !== 'file') continue
      if (!field.required) continue
      const selection = selections.find(s => s.fieldId === field.id)
      if (!selection || !selection.selected) {
        errors.push({
          fieldId: field.id,
          fieldName: field.name ?? 'file_upload',
          severity: 'error',
          message: `Required upload missing: ${field.label ?? 'File'}`,
          category: 'missing_upload',
        })
      }
    }
    return errors
  },

  hasErrors(validations: FieldValidation[]): boolean {
    return validations.some(v => v.severity === 'error')
  },

  hasWarnings(validations: FieldValidation[]): boolean {
    return validations.some(v => v.severity === 'warning')
  },

  createError(field: DetectedField, category: FieldValidation['category'], message: string): FieldValidation {
    return {
      fieldId: field.id,
      fieldName: field.label ?? field.name ?? field.id,
      severity: 'error',
      message,
      category,
    }
  },

  createWarning(field: DetectedField, category: FieldValidation['category'], message: string): FieldValidation {
    return {
      fieldId: field.id,
      fieldName: field.label ?? field.name ?? field.id,
      severity: 'warning',
      message,
      category,
    }
  },
}
