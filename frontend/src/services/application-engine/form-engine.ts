import type { DetectedForm, DetectedField, FormEngineConfig, FormEngineState, SemanticFieldMapping, AIAnswer, FieldValidation, DocumentSelection, MultiStepState, ApprovalPoint, SubmissionResult, ApplicationSummary, AIAnswerRequest, ProfileData } from './types'
import { DEFAULT_FORM_ENGINE_CONFIG } from './types'
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
import { actionEngine } from '../browser/action-engine'
import { locatorEngine } from '../browser/locator-engine'
import type { ProviderId } from '../discovery/types'

interface FillFieldResult {
  fieldId: string
  success: boolean
  error: string | null
}

export class FormEngine {
  private config: FormEngineConfig
  private state: FormEngineState = 'idle'
  private form: DetectedForm | null = null
  private mappings: Map<string, SemanticFieldMapping> = new Map()
  private fieldValues: Record<string, string> = {}
  private aiAnswers: AIAnswer[] = []
  private documents: DocumentSelection[] = []
  private validations: FieldValidation[] = []
  private multiStep: MultiStepState | null = null
  private approvalPoint: ApprovalPoint | null = null
  private summary: ApplicationSummary | null = null
  private profile: ProfileData | null = null

  constructor(config?: Partial<FormEngineConfig>) {
    this.config = { ...DEFAULT_FORM_ENGINE_CONFIG, ...config }
  }

  getState(): FormEngineState {
    return this.state
  }

  getForm(): DetectedForm | null {
    return this.form
  }

  getMappings(): Map<string, SemanticFieldMapping> {
    return this.mappings
  }

  getFieldValues(): Record<string, string> {
    return { ...this.fieldValues }
  }

  getAIAnswers(): AIAnswer[] {
    return [...this.aiAnswers]
  }

  getDocuments(): DocumentSelection[] {
    return [...this.documents]
  }

  getValidations(): FieldValidation[] {
    return [...this.validations]
  }

  getMultiStep(): MultiStepState | null {
    return this.multiStep
  }

  getApprovalPoint(): ApprovalPoint | null {
    return this.approvalPoint
  }

  getSummary(): ApplicationSummary | null {
    return this.summary
  }

  getConfig(): FormEngineConfig {
    return { ...this.config }
  }

  updateConfig(updates: Partial<FormEngineConfig>): void {
    this.config = { ...this.config, ...updates }
  }

  async detectForm(url: string, sessionId: string): Promise<DetectedForm> {
    this.transitionTo('detecting')
    const forms = await fieldDetector.detectForms(url)
    if (forms.length === 0) {
      this.transitionTo('failed')
      throw new Error('No forms detected on the page')
    }

    this.form = forms[0]
    this.multiStep = multiStepCoordinator.analyzeSteps(this.form)
    checkpointService.create(
      sessionId, url, '' as ProviderId, 1, [], {}, [], 'detect'
    )
    this.transitionTo('mapping')
    return this.form
  }

  setProfile(profile: ProfileData): void {
    this.profile = profile
  }

  mapFields(): Map<string, SemanticFieldMapping> {
    if (!this.form) throw new Error('No form detected. Call detectForm first.')

    const fillable = fieldDetector.getFillableFields(this.form.fields)
    const mappingsList = semanticFieldMapper.mapFields(fillable)
    this.mappings = new Map(mappingsList.map(m => [m.fieldId, m]))
    return this.mappings
  }

  async fillFields(sessionId: string, workflowId: string): Promise<FillFieldResult[]> {
    if (!this.form) throw new Error('No form detected')
    if (!this.profile) throw new Error('No profile set. Call setProfile first.')

    this.transitionTo('filling')
    const results: FillFieldResult[] = []
    const fields = this.multiStep && this.multiStep.detected
      ? multiStepCoordinator.getCurrentStepFields(this.form, this.multiStep)
      : fieldDetector.getFillableFields(this.form.fields)

    for (const field of fields) {
      const result = await this.fillSingleField(field, sessionId, workflowId)
      results.push(result)
    }

    return results
  }

  private async fillSingleField(field: DetectedField, sessionId: string, workflowId: string): Promise<FillFieldResult> {
    const mapping = this.mappings.get(field.id)
    const profileValue = mapping && this.profile
      ? profileMapper.mapFieldFromProfile(field, this.profile).value
      : null
    const value = profileValue ?? field.value ?? ''

    try {
      const element = await locatorEngine.findElement(field.selector, 'css', { timeout: 3000 })
      if (!element) {
        return { fieldId: field.id, success: false, error: 'Element not found' }
      }

      switch (field.fieldType) {
        case 'text':
        case 'email':
        case 'phone':
        case 'number':
        case 'url':
        case 'search':
        case 'password':
          await actionEngine.type(element, value, sessionId, {
            delay: this.config.humanizeTyping ? 50 : 0,
          })
          break

        case 'textarea':
          await actionEngine.type(element, value, sessionId)
          break

        case 'dropdown':
        case 'multi_select':
          if (value) {
            await actionEngine.select(element, value, sessionId)
          }
          break

        case 'checkbox':
          if (value === 'true' || value === 'yes') {
            await actionEngine.check(element, sessionId)
          }
          break

        case 'radio': {
          const radioElements = await locatorEngine.findElements(
            `input[type="radio"][name="${field.name}"]`,
            'css'
          )
          for (const radio of radioElements) {
            if (radio.value === value) {
              await actionEngine.click(radio, sessionId)
              break
            }
          }
          break
        }

        case 'file': {
          break
        }

        case 'date':
          await actionEngine.type(element, value, sessionId)
          break
      }

      this.fieldValues[field.id] = value

      checkpointService.save(workflowId, checkpointService.create(
        workflowId, this.form?.url ?? '', '' as ProviderId,
        this.multiStep?.currentStep ?? 1,
        Object.keys(this.fieldValues),
        this.fieldValues, [], 'fill'
      ))

      return { fieldId: field.id, success: true, error: null }
    } catch (err) {
      return {
        fieldId: field.id,
        success: false,
        error: err instanceof Error ? err.message : 'Unknown error',
      }
    }
  }

  async generateAIAnswers(
    questions: { fieldId: string; question: string }[]
  ): Promise<AIAnswer[]> {
    this.transitionTo('ai_generating')
    if (!this.profile) throw new Error('No profile set')

    const context: AIAnswerRequest['context'] = {
      jobTitle: '',
      companyName: '',
      companyDescription: '',
      jobDescription: '',
      requiredSkills: [],
    }

    const aiQuestions = questions.map(q => ({
      fieldId: q.fieldId,
      question: q.question,
      category: answerEngine.inferQuestionCategory(q.question),
    }))

    const answers = answerEngine.generateAnswers(aiQuestions, context, this.profile)
    this.aiAnswers = aiQuestions.map(q => answers.get(q.fieldId) ?? {
      answer: '',
      confidence: 0,
      generated: false,
    })

    return this.aiAnswers
  }

  selectDocuments(
    availableResumes: string[],
    availableCoverLetters: string[],
    availablePortfolios: string[],
    availableCertificates: string[]
  ): DocumentSelection[] {
    if (!this.form) throw new Error('No form detected')
    this.transitionTo('uploading')

    this.documents = documentSelector.selectDocuments(
      this.form.fields,
      availableResumes,
      availableCoverLetters,
      availablePortfolios,
      availableCertificates
    )

    return this.documents
  }

  validate(includeDuplicates: boolean = false): FieldValidation[] {
    if (!this.form) throw new Error('No form detected')

    const allFields = fieldDetector.getFillableFields(this.form.fields)
    this.validations = validationEngine.validateFields(allFields, this.fieldValues, this.mappings)

    if (includeDuplicates) {
      this.validations.push(...validationEngine.checkDuplicateValues(this.fieldValues))
    }

    return this.validations
  }

  async review(): Promise<ApplicationSummary> {
    this.transitionTo('reviewing')

    const validations = this.validate()

    this.summary = applicationSummaryBuilder.build(
      '' as ProviderId,
      '',
      '',
      this.form?.fields ?? [],
      this.mappings,
      this.fieldValues,
      this.aiAnswers,
      this.documents,
      validations,
      this.multiStep ?? { detected: false, totalSteps: 1, currentStep: 1, steps: [], completedSteps: [] }
    )

    return this.summary
  }

  async requestApproval(
    pointType: ApprovalPoint['type'],
    description: string
  ): Promise<ApprovalPoint | null> {
    if (!approvalWorkflow.shouldRequestApproval(this.config.executionMode, pointType, this.config.approvalPoints)) {
      return null
    }

    this.transitionTo('awaiting_approval')
    this.approvalPoint = approvalWorkflow.createApprovalPoint(pointType, description)
    return this.approvalPoint
  }

  approve(): ApprovalPoint | null {
    if (this.approvalPoint) {
      this.approvalPoint = approvalWorkflow.approve(this.approvalPoint)
    }
    return this.approvalPoint
  }

  reject(): ApprovalPoint | null {
    if (this.approvalPoint) {
      this.approvalPoint = approvalWorkflow.reject(this.approvalPoint)
    }
    return this.approvalPoint
  }

  async submit(sessionId: string, providerId: ProviderId, applicationUrl: string): Promise<SubmissionResult> {
    this.transitionTo('submitting')

    if (!this.form) throw new Error('No form detected')
    if (!this.form.submitButton) throw new Error('No submit button detected')

    if (this.config.executionMode !== 'automatic') {
      const approval = await this.requestApproval('before_submission', 'Ready to submit application')
      if (approval && !approvalWorkflow.isApproved(approval)) {
        this.transitionTo('awaiting_approval')
        return {
          success: false,
          applicationUrl,
          confirmationPage: false,
          confirmationMessage: 'Submission awaiting approval',
          applicationId: null,
          duration: 0,
          errors: ['Submission pending approval'],
          providerId,
          timestamp: new Date().toISOString(),
        }
      }
    }

    const result = await submissionManager.submitForm(
      sessionId,
      this.form.submitButton.selector,
      providerId,
      applicationUrl
    )

    this.transitionTo(result.success ? 'completed' : 'failed')
    return result
  }

  canRecover(workflowId: string): boolean {
    return recoveryManager.canRecover(workflowId)
  }

  recover(workflowId: string): Partial<Record<string, unknown>> {
    this.transitionTo('recovering')
    const recovered = recoveryManager.recoverState(workflowId)
    if (recovered.stepIndex && this.form) {
      if (this.multiStep) {
        this.multiStep.currentStep = recovered.stepIndex as number
      }
    }
    if (recovered.fieldValues) {
      this.fieldValues = recovered.fieldValues as Record<string, string>
    }
    return recovered
  }

  getStepProgress(): number {
    if (!this.multiStep) return 100
    return multiStepCoordinator.getStepProgress(this.multiStep)
  }

  advanceStep(): void {
    if (this.multiStep) {
      this.multiStep = multiStepCoordinator.markStepCompleted(this.multiStep, this.multiStep.currentStep)
      this.multiStep = multiStepCoordinator.advanceStep(this.multiStep)
    }
  }

  goBackStep(): void {
    if (this.multiStep) {
      this.multiStep = multiStepCoordinator.goBackStep(this.multiStep)
    }
  }

  reset(): void {
    this.state = 'idle'
    this.form = null
    this.mappings = new Map()
    this.fieldValues = {}
    this.aiAnswers = []
    this.documents = []
    this.validations = []
    this.multiStep = null
    this.approvalPoint = null
    this.summary = null
  }

  private transitionTo(newState: FormEngineState): void {
    this.state = newState
  }
}
