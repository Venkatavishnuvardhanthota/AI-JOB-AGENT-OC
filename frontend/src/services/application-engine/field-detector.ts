import type { DOMElement, FormDetection, FormInput } from '../browser/types'
import type { DetectedField, DetectedFieldType, DetectedForm } from './types'
import { domInspectionService } from '../browser/dom-inspection'
import { locatorEngine } from '../browser/locator-engine'

const INPUT_TYPE_MAP: Record<string, DetectedFieldType> = {
  text: 'text',
  textarea: 'textarea',
  password: 'password',
  email: 'email',
  tel: 'phone',
  number: 'number',
  date: 'date',
  url: 'url',
  select: 'dropdown',
  'select-one': 'dropdown',
  'select-multiple': 'multi_select',
  radio: 'radio',
  checkbox: 'checkbox',
  file: 'file',
  hidden: 'hidden',
  submit: 'submit',
  search: 'search',
}

let fieldCounter = 0

function detectFieldType(elementType: string, htmlType: string, tag: string): DetectedFieldType {
  if (tag === 'textarea') return 'textarea'
  if (tag === 'select') {
    return elementType === 'multi_select' ? 'multi_select' : 'dropdown'
  }
  return INPUT_TYPE_MAP[htmlType] ?? 'text'
}

function buildSelector(element: DOMElement): string {
  if (element.id) return `#${CSS.escape(element.id)}`
  if (element.name) {
    const tag = element.tag.toLowerCase()
    return `${tag}[name="${element.name.replace(/"/g, '\\"')}"]`
  }
  if (element.classes.length > 0) {
    return element.classes.map(c => `.${CSS.escape(c)}`).join('')
  }
  return element.tag.toLowerCase()
}

export const fieldDetector = {
  async detectForms(url: string): Promise<DetectedForm[]> {
    const elements = await locatorEngine.findElements('form, input, select, textarea, button[type="submit"]', 'css', {
      timeout: 5000,
    })

    const formElements = elements.filter(e => e.tag.toLowerCase() === 'form')

    if (formElements.length === 0) {
      const formDetection = domInspectionService.detectForm(elements)
      if (formDetection) {
        const form = this.buildDetectedForm(formDetection, elements, url, 0)
        return form ? [form] : []
      }
      return []
    }

    const forms: DetectedForm[] = []
    for (let i = 0; i < formElements.length; i++) {
      const fe = formElements[i]
      const childElements = elements.filter(e => {
        if (e === fe) return false
        let parent = e as DOMElement | null
        while (parent) {
          if (parent === fe) return true
          parent = null
        }
        return false
      })

      const formDetection = domInspectionService.detectForm([fe, ...childElements])
      if (formDetection) {
        const form = this.buildDetectedForm(formDetection, childElements.length > 0 ? childElements : elements, url, i)
        if (form) forms.push(form)
      }
    }

    return forms
  },

  buildDetectedForm(formDetection: FormDetection, allElements: DOMElement[], url: string, formIndex: number): DetectedForm | null {
    if (!formDetection.inputs || formDetection.inputs.length === 0) return null

    const fields = this.detectFields(formDetection.inputs, allElements)
    const stepInfo = this.detectSteps(allElements, fields)
    const formId = formDetection.formId ?? `form_${formIndex}`

    return {
      id: formId,
      action: formDetection.action,
      method: formDetection.method,
      fields,
      submitButton: formDetection.submitButton
        ? {
            selector: `button:has-text("${formDetection.submitButton.text}")`,
            text: formDetection.submitButton.text,
            enabled: formDetection.submitButton.enabled,
          }
        : null,
      isMultiStep: stepInfo.isMultiStep,
      totalSteps: stepInfo.totalSteps,
      currentStep: stepInfo.currentStep,
      stepIndicators: stepInfo.stepIndicators,
      url,
    }
  },

  detectFields(inputs: FormInput[], elements: DOMElement[]): DetectedField[] {
    fieldCounter = 0
    return inputs.map((input, index) => {
      fieldCounter++
      const element = elements.find(e => e.name === input.name && e.tag.toLowerCase() !== 'form')
      const fieldType = detectFieldType(input.elementType, input.type ?? 'text', element?.tag ?? 'input')

      return {
        id: `field_${fieldCounter}`,
        index,
        fieldType,
        htmlType: input.type ?? 'text',
        elementType: input.elementType,
        name: input.name,
        label: input.label,
        placeholder: input.placeholder,
        required: input.required,
        disabled: !input.enabled,
        readonly: element?.readonly ?? false,
        value: input.value,
        options: input.options,
        attributes: element?.attributes ?? {},
        selector: element ? buildSelector(element) : '',
        stepIndex: null,
      }
    })
  },

  detectSteps(elements: DOMElement[], fields: DetectedField[]): { isMultiStep: boolean; totalSteps: number | null; currentStep: number | null; stepIndicators: string[] } {
    const stepIndicators: string[] = []
    const wizardButtons = elements.filter(e => {
      const text = e.text?.toLowerCase() ?? ''
      return (
        text.includes('next') ||
        text.includes('continue') ||
        text.includes('back') ||
        text.includes('review') ||
        text.includes('step')
      )
    })

    if (wizardButtons.length > 0) {
      const stepElements = elements.filter(e => {
        const text = e.text ?? ''
        return /step\s+\d+/i.test(text) || /^\d+\s*\/\s*\d+$/.test(text)
      })
      stepElements.forEach(se => {
        if (se.text) stepIndicators.push(se.text)
      })
    }

    const stepPattern = elements
      .map(e => e.text ?? '')
      .find(t => /^(step|page)\s+\d+/i.test(t))

    let totalSteps: number | null = null
    let currentStep: number | null = null

    if (stepPattern) {
      const match = stepPattern.match(/(\d+)\s*\/\s*(\d+)/)
      if (match) {
        currentStep = parseInt(match[1])
        totalSteps = parseInt(match[2])
      } else {
        const stepMatch = stepPattern.match(/(?:step|page)\s+(\d+)/i)
        if (stepMatch) currentStep = parseInt(stepMatch[1])
      }
    }

    if (stepIndicators.length >= 2 || wizardButtons.length >= 2) {
      totalSteps = totalSteps ?? stepIndicators.length
    }

    const isMultiStep = stepIndicators.length >= 2 || wizardButtons.length >= 2 || (totalSteps !== null && totalSteps > 1)

    if (isMultiStep && fields.length > 0) {
      const perStep = Math.max(1, Math.floor(fields.length / (totalSteps ?? 2)))
      fields.forEach((f, i) => {
        f.stepIndex = Math.min(Math.floor(i / perStep) + 1, totalSteps ?? 2)
      })
    }

    return { isMultiStep, totalSteps, currentStep, stepIndicators }
  },

  getFieldsByStep(form: DetectedForm, stepIndex: number): DetectedField[] {
    return form.fields.filter(f => f.stepIndex === stepIndex || f.stepIndex === null)
  },

  getVisibleFields(fields: DetectedField[]): DetectedField[] {
    return fields.filter(f => !f.disabled && f.fieldType !== 'hidden' && f.fieldType !== 'submit')
  },

  getFillableFields(fields: DetectedField[]): DetectedField[] {
    return fields.filter(
      f => !f.disabled && !f.readonly && f.fieldType !== 'submit' && f.fieldType !== 'hidden'
    )
  },
}
