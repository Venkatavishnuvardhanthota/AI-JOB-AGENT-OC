import type { DOMElement, FormDetection, FormInput, ElementType } from './types'

export const domInspectionService = {
  detectForm(elements: DOMElement[]): FormDetection | null {
    const formElements = elements.filter(e => e.type === 'form' || e.tag === 'form')
    if (formElements.length === 0) return null

    const form = formElements[0]
    const inputs = this.extractFormInputs(elements)
    const submitBtn = elements.find(e =>
      e.type === 'button' && (e.attributes.type === 'submit' || e.text?.toLowerCase().includes('submit'))
    )

    return {
      formId: form.attributes.id ?? null,
      action: form.attributes.action ?? null,
      method: (form.attributes.method ?? 'get').toUpperCase(),
      inputs,
      submitButton: submitBtn ? { text: submitBtn.text || 'Submit', enabled: submitBtn.enabled } : null,
      isUploadForm: inputs.some(i => i.elementType === 'file'),
    }
  },

  extractFormInputs(elements: DOMElement[]): FormInput[] {
    return elements
      .filter(e => ['input', 'textarea', 'select', 'file', 'checkbox', 'radio'].includes(e.type))
      .map(e => ({
        name: e.name,
        type: e.attributes.type || 'text',
        label: this.findLabel(elements, e),
        placeholder: e.attributes.placeholder ?? null,
        required: e.attributes.required === 'true',
        enabled: e.enabled,
        elementType: e.type,
        value: e.value,
        options: e.type === 'select' ? this.extractOptions(e) : null,
      }))
  },

  findLabel(elements: DOMElement[], element: DOMElement): string | null {
    for (const e of elements) {
      if (e.tag === 'label' && e.attributes.for === element.id) return e.text
    }
    return element.attributes['aria-label'] ?? null
  },

  extractOptions(element: DOMElement): string[] | null {
    if (!element.children) return null
    return element.children
      .filter(c => c.tag === 'option')
      .map(c => c.text || c.value || '')
      .filter(Boolean)
  },

  classifyElement(tag: string, attrs: Record<string, string>): ElementType {
    const type = (attrs.type || '').toLowerCase()
    const role = (attrs.role || '').toLowerCase()

    if (tag === 'form') return 'form'
    if (tag === 'iframe') return 'iframe'
    if (tag === 'a' || tag === 'link') return 'link'
    if (tag === 'button' || (tag === 'input' && type === 'submit') || (tag === 'input' && type === 'button') || role === 'button') return 'button'
    if (tag === 'input' && type === 'file') return 'file'
    if (tag === 'input' && type === 'checkbox') return 'checkbox'
    if (tag === 'input' && type === 'radio') return 'radio'
    if (tag === 'select') return 'dropdown'
    if (tag === 'textarea') return 'textarea'
    if (tag === 'input') return 'input'
    if (tag === 'option') return 'unknown'
    if (role) return role as ElementType
    return 'unknown'
  },

  createElementSnapshot(tag: string, attrs: Record<string, string>, text: string | null): DOMElement {
    return {
      tag,
      type: this.classifyElement(tag, attrs),
      attributes: attrs,
      text,
      rect: null,
      visible: true,
      enabled: attrs.disabled !== 'true',
      readonly: attrs.readonly === 'true',
      checked: attrs.checked === 'true' ? true : null,
      selected: null,
      value: attrs.value ?? null,
      name: attrs.name ?? null,
      id: attrs.id ?? null,
      classes: (attrs.class || '').split(/\s+/).filter(Boolean),
      aria: this.extractAria(attrs),
      children: [],
      shadowRoot: false,
      iframeContent: null,
    }
  },

  extractAria(attrs: Record<string, string>): Record<string, string> | null {
    const aria: Record<string, string> = {}
    for (const [key, value] of Object.entries(attrs)) {
      if (key.startsWith('aria-')) aria[key] = value
    }
    return Object.keys(aria).length > 0 ? aria : null
  },
}
