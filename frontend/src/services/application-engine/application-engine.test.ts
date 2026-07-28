import { describe, it, expect, beforeEach } from 'vitest'
import { fieldDetector } from './field-detector'
import { semanticFieldMapper } from './semantic-field-mapper'
import { profileMapper } from './profile-mapper'
import { answerEngine } from './answer-engine'
import { documentSelector } from './document-selector'
import { validationEngine } from './validation-engine'
import { multiStepCoordinator } from './multi-step-coordinator'
import { checkpointService } from './checkpoints'
import { recoveryManager } from './recovery-manager'
import { approvalWorkflow } from './approval-workflow'
import { submissionManager } from './submission-manager'
import { applicationSummaryBuilder } from './application-summary'
import { FormEngine } from './form-engine'
import { ApplicationEngine } from './application-engine'
import type { DetectedField, DetectedForm, ProfileData, MultiStepState, SemanticFieldMapping } from './types'

function makeField(overrides: Partial<DetectedField> = {}): DetectedField {
  return {
    id: 'field_1',
    index: 0,
    fieldType: 'text',
    htmlType: 'text',
    elementType: 'input',
    name: null,
    label: null,
    placeholder: null,
    required: false,
    disabled: false,
    readonly: false,
    value: null,
    options: null,
    attributes: {},
    selector: 'input',
    stepIndex: null,
    ...overrides,
  }
}

function makeForm(overrides: Partial<DetectedForm> = {}): DetectedForm {
  return {
    id: 'form_1',
    action: '/apply',
    method: 'POST',
    fields: [makeField({ id: 'field_1', label: 'Full Name', name: 'name' })],
    submitButton: { selector: 'button[type="submit"]', text: 'Submit', enabled: true },
    isMultiStep: false,
    totalSteps: null,
    currentStep: null,
    stepIndicators: [],
    url: 'https://example.com/apply',
    ...overrides,
  }
}

const SAMPLE_PROFILE: ProfileData = {
  firstName: 'John',
  lastName: 'Doe',
  email: 'john@example.com',
  phone: '+1-555-1234',
  headline: 'Senior Software Engineer',
  bio: 'Experienced developer',
  location: 'San Francisco, CA',
  portfolioUrl: 'https://portfolio.dev',
  linkedinUrl: 'https://linkedin.com/in/johndoe',
  githubUrl: 'https://github.com/johndoe',
  website: 'https://johndoe.dev',
  currentCompany: 'TechCorp',
  currentRole: 'Senior Engineer',
  yearsOfExperience: '8',
  expectedSalary: '150000',
  currentSalary: '130000',
  salaryMin: '',
  salaryMax: '',
  salaryCurrency: '',
  noticePeriod: '30 days',
  workAuthorization: 'US Citizen',
  visaStatus: '',
  education: [{ institution: 'MIT', degree: 'BS', fieldOfStudy: 'CS', startDate: '2012', endDate: '2016', gpa: '3.8' }],
  experience: [{ company: 'TechCorp', title: 'Senior Engineer', location: 'SF', startDate: '2018', endDate: '', isCurrent: true, description: 'Built stuff' }],
  projects: [{ name: 'Project X', description: 'A project', url: '', technologies: ['React'] }],
  skills: ['React', 'TypeScript', 'Node.js'],
  certifications: [{ name: 'AWS', issuer: 'Amazon', issueDate: '2023', credentialUrl: '' }],
  languages: [{ name: 'English', proficiency: 'Native' }],
}

describe('ApplicationEngine', () => {
  it('creates an engine and returns its id', () => {
    const ae = new ApplicationEngine()
    ae.setProfile({ firstName: 'Test' })
    const engine = ae.createEngine('test_engine')
    expect(engine).toBeDefined()
    expect(ae.listEngines()).toContain('test_engine')
  })

  it('removes an engine', () => {
    const ae = new ApplicationEngine()
    ae.setProfile({ firstName: 'Test' })
    ae.createEngine('test_engine')
    expect(ae.removeEngine('test_engine')).toBe(true)
    expect(ae.listEngines()).not.toContain('test_engine')
  })

  it('setProfile builds a full profile from partial data', () => {
    const ae = new ApplicationEngine()
    ae.setProfile({ firstName: 'Jane' }, [], [], [], ['React'], [], [])
    const profile = ae.getProfile()
    expect(profile).not.toBeNull()
    expect(profile!.firstName).toBe('Jane')
    expect(profile!.skills).toContain('React')
  })

  it('resetAll clears all engines and profile', () => {
    const ae = new ApplicationEngine()
    ae.setProfile({ firstName: 'Test' })
    ae.createEngine('e1')
    ae.createEngine('e2')
    ae.resetAll()
    expect(ae.listEngines()).toHaveLength(0)
    expect(ae.getProfile()).toBeNull()
  })
})

describe('FormEngine', () => {
  let engine: FormEngine

  beforeEach(() => {
    engine = new FormEngine()
  })

  it('starts in idle state', () => {
    expect(engine.getState()).toBe('idle')
  })

  it('uses default config', () => {
    const config = engine.getConfig()
    expect(config.executionMode).toBe('manual_approval')
    expect(config.fillDelay).toBe(500)
  })

  it('updateConfig merges with defaults', () => {
    engine.updateConfig({ executionMode: 'automatic' })
    expect(engine.getConfig().executionMode).toBe('automatic')
    expect(engine.getConfig().fillDelay).toBe(500)
  })

  it('setProfile stores profile', () => {
    engine.setProfile(SAMPLE_PROFILE)
    expect(engine.getState()).toBe('idle')
  })

  it('mapFields throws if no form detected', () => {
    expect(() => engine.mapFields()).toThrow('No form detected')
  })

  it('mapFields returns empty map for no fillable fields', () => {
    const form = makeForm({ fields: [makeField({ fieldType: 'hidden' })] })
    engine['form'] = form
    const mappings = engine.mapFields()
    expect(mappings.size).toBe(0)
  })

  it('mapFields returns mappings for text fields', () => {
    const form = makeForm({
      fields: [
        makeField({ id: 'f1', label: 'Full Name', fieldType: 'text' }),
        makeField({ id: 'f2', label: 'Email', fieldType: 'email' }),
      ],
    })
    engine['form'] = form
    const mappings = engine.mapFields()
    expect(mappings.has('f1')).toBe(true)
    expect(mappings.has('f2')).toBe(true)
  })

  it('advanceStep moves to next step', () => {
    engine['multiStep'] = {
      detected: true,
      totalSteps: 3,
      currentStep: 1,
      steps: [
        { index: 1, label: 'Step 1', fields: [], completed: false },
        { index: 2, label: 'Step 2', fields: [], completed: false },
        { index: 3, label: 'Step 3', fields: [], completed: false },
      ],
      completedSteps: [],
    }
    engine.advanceStep()
    expect(engine.getMultiStep()!.currentStep).toBe(2)
  })

  it('goBackStep returns to previous step', () => {
    engine['multiStep'] = {
      detected: true,
      totalSteps: 3,
      currentStep: 2,
      steps: [
        { index: 1, label: 'Step 1', fields: [], completed: false },
        { index: 2, label: 'Step 2', fields: [], completed: false },
        { index: 3, label: 'Step 3', fields: [], completed: false },
      ],
      completedSteps: [],
    }
    engine.goBackStep()
    expect(engine.getMultiStep()!.currentStep).toBe(1)
  })

  it('getStepProgress returns 100 for single-step forms', () => {
    expect(engine.getStepProgress()).toBe(100)
  })

  it('reset clears all state', () => {
    engine.setProfile(SAMPLE_PROFILE)
    engine['form'] = makeForm()
    engine.mapFields()
    engine.reset()
    expect(engine.getForm()).toBeNull()
    expect(engine.getMappings().size).toBe(0)
    expect(engine.getState()).toBe('idle')
  })

  it('validate checks required fields', () => {
    const form = makeForm({
      fields: [
        makeField({ id: 'f1', label: 'Name', required: true, fieldType: 'text' }),
      ],
    })
    engine['form'] = form
    engine['fieldValues'] = { f1: '' }
    const errors = engine.validate()
    expect(errors.length).toBeGreaterThan(0)
    expect(errors[0].severity).toBe('error')
    expect(errors[0].category).toBe('required')
  })

  it('validate passes when required fields have values', () => {
    const form = makeForm({
      fields: [
        makeField({ id: 'f1', label: 'Name', required: true, fieldType: 'text' }),
      ],
    })
    engine['form'] = form
    engine['fieldValues'] = { f1: 'John' }
    const errors = engine.validate()
    const requiredErrors = errors.filter(e => e.category === 'required')
    expect(requiredErrors.length).toBe(0)
  })

  it('approve marks approval point as approved', () => {
    engine['approvalPoint'] = { id: 'ap1', type: 'before_submission', description: 'Test', status: 'pending' }
    engine.approve()
    expect(engine.getApprovalPoint()!.status).toBe('approved')
  })

  it('reject marks approval point as rejected', () => {
    engine['approvalPoint'] = { id: 'ap1', type: 'before_submission', description: 'Test', status: 'pending' }
    engine.reject()
    expect(engine.getApprovalPoint()!.status).toBe('rejected')
  })
})

describe('fieldDetector', () => {
  it('detectFields returns correct types', () => {
    const inputs = [
      { name: 'email', type: 'email', label: 'Email', placeholder: null, required: true, enabled: true, elementType: 'input' as const, value: null, options: null },
      { name: 'phone', type: 'tel', label: 'Phone', placeholder: null, required: false, enabled: true, elementType: 'input' as const, value: null, options: null },
    ]
    const elements = [
      { tag: 'input', attributes: { type: 'email' }, name: 'email' } as any,
      { tag: 'input', attributes: { type: 'tel' }, name: 'phone' } as any,
    ]
    const fields = fieldDetector.detectFields(inputs, elements)
    expect(fields).toHaveLength(2)
    expect(fields[0].fieldType).toBe('email')
    expect(fields[1].fieldType).toBe('phone')
  })

  it('getVisibleFields excludes hidden and submit', () => {
    const fields = [
      makeField({ id: 'f1', fieldType: 'text' }),
      makeField({ id: 'f2', fieldType: 'hidden' }),
      makeField({ id: 'f3', fieldType: 'submit' }),
      makeField({ id: 'f4', disabled: true }),
    ]
    const visible = fieldDetector.getVisibleFields(fields)
    expect(visible.map(f => f.id)).toEqual(['f1'])
  })

  it('getFillableFields excludes disabled, readonly, submit, hidden', () => {
    const fields = [
      makeField({ id: 'f1', fieldType: 'text' }),
      makeField({ id: 'f2', disabled: true }),
      makeField({ id: 'f3', readonly: true }),
      makeField({ id: 'f4', fieldType: 'submit' }),
    ]
    const fillable = fieldDetector.getFillableFields(fields)
    expect(fillable.map(f => f.id)).toEqual(['f1'])
  })

  it('detectSteps detects wizard forms', () => {
    const result = fieldDetector.detectSteps(
      [{ text: 'Next', tag: 'button' } as any, { text: 'Back', tag: 'button' } as any],
      []
    )
    expect(result.isMultiStep).toBe(true)
  })

  it('detectSteps returns single step for simple forms', () => {
    const result = fieldDetector.detectSteps([], [])
    expect(result.isMultiStep).toBe(false)
    expect(result.totalSteps).toBeNull()
  })
})

describe('semanticFieldMapper', () => {
  it('maps email field correctly', () => {
    const field = makeField({ id: 'f1', label: 'Email Address', name: 'email', fieldType: 'email' })
    const mapping = semanticFieldMapper.getMappingForField(field)
    expect(mapping.category).toBe('email')
    expect(mapping.profilePath).toBe('email')
    expect(mapping.confidence).toBeGreaterThan(0)
  })

  it('maps first name field correctly', () => {
    const field = makeField({ id: 'f2', label: 'First Name', name: 'first_name', fieldType: 'text' })
    const mapping = semanticFieldMapper.getMappingForField(field)
    expect(mapping.category).toBe('first_name')
    expect(mapping.profilePath).toBe('firstName')
  })

  it('maps phone field correctly', () => {
    const field = makeField({ id: 'f3', label: 'Phone Number', name: 'phone', fieldType: 'phone' })
    const mapping = semanticFieldMapper.getMappingForField(field)
    expect(mapping.category).toBe('phone')
  })

  it('maps unknown field as custom', () => {
    const field = makeField({ id: 'f4', label: 'Random Custom Field', name: 'custom_xyz', fieldType: 'text' })
    const mapping = semanticFieldMapper.getMappingForField(field)
    expect(mapping.category).toBe('custom')
    expect(mapping.confidence).toBeLessThan(0.3)
  })

  it('mapFields returns mappings for all fields', () => {
    const fields = [
      makeField({ id: 'f1', label: 'Email', fieldType: 'email' }),
      makeField({ id: 'f2', label: 'Phone', fieldType: 'phone' }),
      makeField({ id: 'f3', label: 'Full Name', fieldType: 'text' }),
    ]
    const mappings = semanticFieldMapper.mapFields(fields)
    expect(mappings).toHaveLength(3)
    expect(mappings[0].category).toBe('email')
  })

  it('maps linkedin field correctly', () => {
    const field = makeField({ id: 'f5', label: 'LinkedIn URL', name: 'linkedin_url', fieldType: 'url' })
    const mapping = semanticFieldMapper.getMappingForField(field)
    expect(mapping.category).toBe('linkedin')
  })

  it('maps work authorization field correctly', () => {
    const field = makeField({ id: 'f6', label: 'Work Authorization', name: 'authorization', fieldType: 'text' })
    const mapping = semanticFieldMapper.getMappingForField(field)
    expect(mapping.category).toBe('work_authorization')
  })
})

describe('profileMapper', () => {
  it('builds empty profile when no data provided', () => {
    const profile = profileMapper.buildProfile()
    expect(profile.firstName).toBe('')
    expect(profile.skills).toEqual([])
  })

  it('buildProfile merges sections', () => {
    const profile = profileMapper.buildProfile(
      { firstName: 'John' },
      [{ institution: 'MIT', degree: 'BS', fieldOfStudy: 'CS', startDate: '2016', endDate: '2020', gpa: '3.5' }],
      [{ company: 'Google', title: 'SWE', location: 'NYC', startDate: '2020', endDate: '', isCurrent: true, description: '' }],
      [{ name: 'Project A', description: '', url: '', technologies: [] }],
      ['TypeScript'],
      [{ name: 'AWS Cert', issuer: 'Amazon', issueDate: '2023', credentialUrl: '' }],
      [{ name: 'English', proficiency: 'Native' }]
    )
    expect(profile.firstName).toBe('John')
    expect(profile.education).toHaveLength(1)
    expect(profile.experience).toHaveLength(1)
    expect(profile.skills).toContain('TypeScript')
  })

  it('mapFieldFromProfile maps email field', () => {
    const field = makeField({ id: 'f1', label: 'Email', fieldType: 'email' })
    const result = profileMapper.mapFieldFromProfile(field, SAMPLE_PROFILE)
    expect(result.value).toBe('john@example.com')
    expect(result.source).toBe('profile')
  })

  it('mapFieldFromProfile returns empty for unknown fields', () => {
    const field = makeField({ id: 'f2', label: 'Random Field', fieldType: 'text' })
    const result = profileMapper.mapFieldFromProfile(field, SAMPLE_PROFILE)
    expect(result.value).toBeNull()
    expect(result.source).toBe('empty')
  })

  it('getProfileCompleteness returns percentage', () => {
    const completeness = profileMapper.getProfileCompleteness(SAMPLE_PROFILE)
    expect(completeness.percentage).toBeGreaterThan(0)
    expect(completeness.total).toBeGreaterThan(0)
  })

  it('getProfileCompleteness returns lower for empty profile', () => {
    const empty = profileMapper.buildProfile()
    const completeness = profileMapper.getProfileCompleteness(empty)
    expect(completeness.percentage).toBeLessThan(20)
  })
})

describe('answerEngine', () => {
  it('generates about_yourself answer', () => {
    const answer = answerEngine.generateAnswer({
      fieldCategory: 'bio',
      question: 'Tell us about yourself',
      context: { jobTitle: 'Engineer', companyName: 'Co', companyDescription: '', jobDescription: '', requiredSkills: ['React'] },
      profile: SAMPLE_PROFILE,
    })
    expect(answer.answer).toBeTruthy()
    expect(answer.generated).toBe(true)
    expect(answer.confidence).toBeGreaterThan(0)
  })

  it('generates why_company answer', () => {
    const answer = answerEngine.generateAnswer({
      fieldCategory: 'bio',
      question: 'Why do you want to work here?',
      context: { jobTitle: 'Engineer', companyName: 'Co', companyDescription: 'A great company', jobDescription: '', requiredSkills: ['React'] },
      profile: SAMPLE_PROFILE,
    })
    expect(answer.answer).toContain('Co')
    expect(answer.generated).toBe(true)
  })

  it('generates expected_salary from profile', () => {
    const answer = answerEngine.generateAnswer({
      fieldCategory: 'expected_salary',
      question: 'What is your expected salary?',
      context: { jobTitle: 'Engineer', companyName: 'Co', companyDescription: '', jobDescription: '', requiredSkills: [] },
      profile: SAMPLE_PROFILE,
    })
    expect(answer.answer).toBe('150000')
  })

  it('returns low confidence for unknown questions', () => {
    const answer = answerEngine.generateAnswer({
      fieldCategory: 'custom',
      question: 'What is your favorite color?',
      context: { jobTitle: '', companyName: '', companyDescription: '', jobDescription: '', requiredSkills: [] },
      profile: SAMPLE_PROFILE,
    })
    expect(answer.generated).toBe(false)
    expect(answer.confidence).toBeLessThan(0.5)
  })

  it('inferQuestionCategory identifies category from question text', () => {
    const cat = answerEngine.inferQuestionCategory('Why do you want to work here?')
    expect(cat).toBeDefined()
  })
})

describe('documentSelector', () => {
  it('selects resume when file field has resume label', () => {
    const fields = [makeField({ id: 'f1', label: 'Resume Upload', fieldType: 'file' })]
    const docs = documentSelector.selectDocuments(fields, ['resume.pdf'], [], [], [])
    expect(docs).toHaveLength(1)
    expect(docs[0].type).toBe('resume')
    expect(docs[0].selected).toBe(true)
  })

  it('does not select cover letter if none available', () => {
    const fields = [
      makeField({ id: 'f1', label: 'Cover Letter', fieldType: 'file' }),
    ]
    const docs = documentSelector.selectDocuments(fields, ['resume.pdf'], [], [], [])
    const coverLetter = docs.find(d => d.type === 'cover_letter')
    expect(coverLetter).toBeUndefined()
  })

  it('selects cover letter when available', () => {
    const fields = [makeField({ id: 'f1', label: 'Cover Letter', fieldType: 'file' })]
    const docs = documentSelector.selectDocuments(fields, ['resume.pdf'], ['cover.pdf'], [], [])
    expect(docs.find(d => d.type === 'cover_letter')?.selected).toBe(true)
  })

  it('isResumeField detects resume fields', () => {
    expect(documentSelector.isResumeField(makeField({ label: 'Upload Resume', fieldType: 'file' }))).toBe(true)
    expect(documentSelector.isResumeField(makeField({ label: 'Phone', fieldType: 'text' }))).toBe(false)
  })
})

describe('validationEngine', () => {
  it('validates required field with empty value', () => {
    const field = makeField({ id: 'f1', label: 'Name', required: true, fieldType: 'text' })
    const result = validationEngine.validateField(field, '', null)
    expect(result).not.toBeNull()
    expect(result!.severity).toBe('error')
    expect(result!.category).toBe('required')
  })

  it('validates email format', () => {
    const field = makeField({ id: 'f2', fieldType: 'email' })
    const result = validationEngine.validateField(field, 'invalid-email', null)
    expect(result).not.toBeNull()
    expect(result!.category).toBe('format')
  })

  it('passes valid email', () => {
    const field = makeField({ id: 'f2', fieldType: 'email' })
    const result = validationEngine.validateField(field, 'test@example.com', null)
    expect(result).toBeNull()
  })

  it('validates url format', () => {
    const field = makeField({ id: 'f3', fieldType: 'url' })
    const result = validationEngine.validateField(field, 'not-a-url', null)
    expect(result).not.toBeNull()
    expect(result!.category).toBe('format')
  })

  it('passes valid url', () => {
    const field = makeField({ id: 'f3', fieldType: 'url' })
    const result = validationEngine.validateField(field, 'https://example.com', null)
    expect(result).toBeNull()
  })

  it('detects duplicate values', () => {
    const errors = validationEngine.checkDuplicateValues({ f1: 'same', f2: 'same', f3: 'different' })
    expect(errors.length).toBeGreaterThanOrEqual(2)
  })

  it('hasErrors detects errors', () => {
    const errors = [validationEngine.createError(makeField({}), 'required', 'Test error')]
    expect(validationEngine.hasErrors(errors)).toBe(true)
  })

  it('hasWarnings detects warnings', () => {
    const warnings = [validationEngine.createWarning(makeField({}), 'format', 'Test warning')]
    expect(validationEngine.hasWarnings(warnings)).toBe(true)
  })
})

describe('multiStepCoordinator', () => {
  it('returns single step for non-multi-step form', () => {
    const form = makeForm()
    const state = multiStepCoordinator.analyzeSteps(form)
    expect(state.detected).toBe(false)
    expect(state.totalSteps).toBe(1)
  })

  it('isLastStep returns correct value', () => {
    const state: MultiStepState = { detected: true, totalSteps: 3, currentStep: 3, steps: [], completedSteps: [1, 2] }
    expect(multiStepCoordinator.isLastStep(state)).toBe(true)
    expect(multiStepCoordinator.isFirstStep(state)).toBe(false)
  })

  it('markStepCompleted records completion', () => {
    const state: MultiStepState = {
      detected: true,
      totalSteps: 2,
      currentStep: 1,
      steps: [
        { index: 1, label: 'Step 1', fields: ['f1'], completed: false },
        { index: 2, label: 'Step 2', fields: ['f2'], completed: false },
      ],
      completedSteps: [],
    }
    const updated = multiStepCoordinator.markStepCompleted(state, 1)
    expect(updated.completedSteps).toContain(1)
  })

  it('getStepProgress calculates correctly', () => {
    const state: MultiStepState = { detected: true, totalSteps: 4, currentStep: 2, steps: [], completedSteps: [1, 2] }
    expect(multiStepCoordinator.getStepProgress(state)).toBe(50)
  })
})

describe('checkpointService', () => {
  beforeEach(() => localStorage.clear())

  it('saves and retrieves checkpoints', () => {
    const ckpt = checkpointService.create('wf1', 'https://example.com', 'linkedin', 1, ['f1'], { f1: 'John' }, [], 'fill')
    checkpointService.save('wf1', ckpt)
    const latest = checkpointService.getLatest('wf1')
    expect(latest).not.toBeNull()
    expect(latest!.applicationUrl).toBe('https://example.com')
    expect(latest!.fieldValues.f1).toBe('John')
  })

  it('getAll returns all checkpoints', () => {
    const ckpt1 = checkpointService.create('wf1', 'url1', 'linkedin', 1, [], {}, [], 'fill')
    const ckpt2 = checkpointService.create('wf1', 'url2', 'linkedin', 2, [], {}, [], 'fill')
    checkpointService.save('wf1', ckpt1)
    checkpointService.save('wf1', ckpt2)
    expect(checkpointService.getAll('wf1')).toHaveLength(2)
  })

  it('getByStep returns specific step', () => {
    const ckpt = checkpointService.create('wf1', 'url', 'linkedin', 2, [], {}, [], 'fill')
    checkpointService.save('wf1', ckpt)
    const found = checkpointService.getByStep('wf1', 2)
    expect(found).not.toBeNull()
    expect(checkpointService.getByStep('wf1', 99)).toBeNull()
  })

  it('deleteAll removes all checkpoints', () => {
    const ckpt = checkpointService.create('wf1', 'url', 'linkedin', 1, [], {}, [], 'fill')
    checkpointService.save('wf1', ckpt)
    checkpointService.deleteAll('wf1')
    expect(checkpointService.getAll('wf1')).toHaveLength(0)
  })
})

describe('recoveryManager', () => {
  beforeEach(() => localStorage.clear())

  it('canRecover returns false when no checkpoints', () => {
    expect(recoveryManager.canRecover('wf_none')).toBe(false)
  })

  it('canRecover returns true when checkpoint exists', () => {
    const ckpt = checkpointService.create('wf1', 'url', 'linkedin', 2, ['f1'], { f1: 'John' }, [], 'fill')
    checkpointService.save('wf1', ckpt)
    expect(recoveryManager.canRecover('wf1')).toBe(true)
  })

  it('getRecoveryPlan returns correct next state', () => {
    const ckpt = checkpointService.create('wf1', 'url', 'linkedin', 2, ['f1'], { f1: 'John' }, [], 'fill')
    checkpointService.save('wf1', ckpt)
    const plan = recoveryManager.getRecoveryPlan('wf1')
    expect(plan.canRecover).toBe(true)
    expect(plan.nextState).toBe('filling')
  })
})

describe('approvalWorkflow', () => {
  it('shouldRequestApproval returns false for automatic mode', () => {
    const result = approvalWorkflow.shouldRequestApproval('automatic', 'before_submission', ['before_submission'])
    expect(result).toBe(false)
  })

  it('shouldRequestApproval returns true for manual mode with matching point', () => {
    const result = approvalWorkflow.shouldRequestApproval('manual_approval', 'before_submission', ['before_submission'])
    expect(result).toBe(true)
  })

  it('shouldRequestApproval returns false for unconfigured point', () => {
    const result = approvalWorkflow.shouldRequestApproval('manual_approval', 'before_upload', ['before_submission'])
    expect(result).toBe(false)
  })

  it('approve/reject change status', () => {
    const point = approvalWorkflow.createApprovalPoint('before_submission', 'Test')
    expect(point.status).toBe('pending')

    const approved = approvalWorkflow.approve(point)
    expect(approved.status).toBe('approved')

    const rejected = approvalWorkflow.reject(point)
    expect(rejected.status).toBe('rejected')
  })
})

describe('applicationSummaryBuilder', () => {
  it('build returns summary structure', () => {
    const mappings = new Map<string, SemanticFieldMapping>()
    mappings.set('field_1', { fieldId: 'field_1', category: 'full_name', confidence: 0.9, profilePath: null, defaultValue: null })

    const state: MultiStepState = { detected: false, totalSteps: 1, currentStep: 1, steps: [{ index: 1, label: 'Form', fields: ['field_1'], completed: false }], completedSteps: [] }

    const summary = applicationSummaryBuilder.build(
      'linkedin',
      'Software Engineer',
      'TechCorp',
      [makeField({ id: 'field_1', label: 'Full Name' })],
      mappings,
      { field_1: 'John Doe' },
      [],
      [],
      [],
      state,
    )
    expect(summary.jobTitle).toBe('Software Engineer')
    expect(summary.companyName).toBe('TechCorp')
    expect(summary.fields).toHaveLength(1)
    expect(summary.fields[0].value).toBe('John Doe')
    expect(summary.ready).toBe(true)
  })

  it('isReady returns false when there are validation errors', () => {
    const state: MultiStepState = { detected: false, totalSteps: 1, currentStep: 1, steps: [], completedSteps: [] }
    const validation = [{
      fieldId: 'f1', fieldName: 'Name', severity: 'error' as const, message: 'Required', category: 'required' as const,
    }]
    const summary = applicationSummaryBuilder.build(
      'linkedin', 'Job', 'Co', [], new Map(), {}, [], [], validation, state,
    )
    expect(applicationSummaryBuilder.isReady(summary)).toBe(false)
  })
})

describe('submissionManager', () => {
  it('detectConfirmation handles missing page text gracefully', async () => {
    const result = await submissionManager.detectConfirmation()
    expect(result).toBeDefined()
    expect(typeof result.confirmed).toBe('boolean')
  })
})
