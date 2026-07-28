import type { ElementType } from '../browser/types'
import type { ProviderId } from '../discovery/types'

export type DetectedFieldType =
  | 'text' | 'textarea' | 'password' | 'email' | 'phone' | 'number'
  | 'date' | 'url' | 'dropdown' | 'radio' | 'checkbox' | 'multi_select'
  | 'autocomplete' | 'search' | 'file' | 'hidden' | 'submit'

export interface DetectedField {
  id: string
  index: number
  fieldType: DetectedFieldType
  htmlType: string
  elementType: ElementType
  name: string | null
  label: string | null
  placeholder: string | null
  required: boolean
  disabled: boolean
  readonly: boolean
  value: string | null
  options: string[] | null
  attributes: Record<string, string>
  selector: string
  stepIndex: number | null
}

export interface DetectedForm {
  id: string
  action: string | null
  method: string | null
  fields: DetectedField[]
  submitButton: { selector: string; text: string; enabled: boolean } | null
  isMultiStep: boolean
  totalSteps: number | null
  currentStep: number | null
  stepIndicators: string[]
  url: string
}

export type SemanticFieldCategory =
  | 'first_name' | 'last_name' | 'full_name' | 'email' | 'phone'
  | 'current_company' | 'current_role' | 'years_experience'
  | 'expected_salary' | 'current_salary' | 'notice_period'
  | 'location' | 'address' | 'country' | 'state' | 'city' | 'zip_code'
  | 'university' | 'degree' | 'graduation_year'
  | 'portfolio' | 'github' | 'linkedin' | 'website'
  | 'visa_status' | 'work_authorization'
  | 'cover_letter' | 'resume'
  | 'headline' | 'bio' | 'skills'
  | 'certification' | 'language'
  | 'start_date' | 'end_date'
  | 'how_did_you_hear'
  | 'gender' | 'ethnicity' | 'veteran_status' | 'disability_status'
  | 'linkedin_profile' | 'personal_website'
  | 'salary_min' | 'salary_max' | 'salary_currency'
  | 'linkedin_url'
  | 'custom'

export interface SemanticFieldMapping {
  fieldId: string
  category: SemanticFieldCategory
  confidence: number
  profilePath: string | null
  defaultValue: string | null
}

export interface ProfileData {
  firstName: string
  lastName: string
  email: string
  phone: string
  headline: string
  bio: string
  location: string
  portfolioUrl: string
  linkedinUrl: string
  githubUrl: string
  website: string
  currentCompany: string
  currentRole: string
  yearsOfExperience: string
  expectedSalary: string
  currentSalary: string
  salaryMin: string
  salaryMax: string
  salaryCurrency: string
  noticePeriod: string
  workAuthorization: string
  visaStatus: string
  education: ProfileEducation[]
  experience: ProfileExperience[]
  projects: ProfileProject[]
  skills: string[]
  certifications: ProfileCertification[]
  languages: ProfileLanguage[]
}

export interface ProfileEducation {
  institution: string
  degree: string
  fieldOfStudy: string
  startDate: string
  endDate: string
  gpa: string
}

export interface ProfileExperience {
  company: string
  title: string
  location: string
  startDate: string
  endDate: string
  isCurrent: boolean
  description: string
}

export interface ProfileProject {
  name: string
  description: string
  url: string
  technologies: string[]
}

export interface ProfileCertification {
  name: string
  issuer: string
  issueDate: string
  credentialUrl: string
}

export interface ProfileLanguage {
  name: string
  proficiency: string
}

export interface AIAnswerRequest {
  fieldCategory: SemanticFieldCategory
  question: string
  context: {
    jobTitle: string
    companyName: string
    companyDescription: string
    jobDescription: string
    requiredSkills: string[]
  }
  profile: ProfileData
}

export interface AIAnswer {
  answer: string
  confidence: number
  generated: boolean
}

export interface DocumentSelection {
  type: 'resume' | 'cover_letter' | 'portfolio' | 'certificate' | 'other'
  name: string
  filePath: string | null
  fileData: string | null
  mimeType: string
  required: boolean
  selected: boolean
}

export type ValidationSeverity = 'error' | 'warning' | 'info'

export interface FieldValidation {
  fieldId: string
  fieldName: string
  severity: ValidationSeverity
  message: string
  category: 'required' | 'format' | 'value' | 'missing_upload' | 'duplicate' | 'unsupported'
}

export interface MultiStepState {
  detected: boolean
  totalSteps: number
  currentStep: number
  steps: MultiStepInfo[]
  completedSteps: number[]
}

export interface MultiStepInfo {
  index: number
  label: string
  fields: string[]
  completed: boolean
}

export interface Checkpoint {
  id: string
  workflowId: string
  applicationUrl: string
  providerId: ProviderId
  stepIndex: number
  completedFields: string[]
  fieldValues: Record<string, string>
  uploadedDocuments: string[]
  lastAction: string
  timestamp: string
}

export interface ApprovalPoint {
  id: string
  type: 'before_upload' | 'before_ai_answers' | 'before_submission' | 'on_validation_warning'
  description: string
  status: 'pending' | 'approved' | 'rejected'
}

export interface SubmissionResult {
  success: boolean
  applicationUrl: string
  confirmationPage: boolean
  confirmationMessage: string | null
  applicationId: string | null
  duration: number
  errors: string[]
  providerId: ProviderId
  timestamp: string
}

export interface ApplicationSummary {
  providerId: ProviderId
  jobTitle: string
  companyName: string
  fields: ApplicationSummaryField[]
  aiAnswers: number
  documentsSelected: number
  validationErrors: number
  validationWarnings: number
  totalSteps: number
  currentStep: number
  ready: boolean
}

export interface ApplicationSummaryField {
  fieldName: string
  category: SemanticFieldCategory
  value: string | null
  mapped: boolean
  validated: boolean
  source: 'profile' | 'ai' | 'document' | 'manual' | 'empty'
}

export type FormEngineState =
  | 'idle' | 'navigating' | 'detecting' | 'mapping'
  | 'filling' | 'ai_generating' | 'uploading'
  | 'reviewing' | 'awaiting_approval' | 'submitting'
  | 'completed' | 'failed' | 'recovering'

export type ExecutionMode = 'automatic' | 'manual_approval'

export interface FormEngineConfig {
  executionMode: ExecutionMode
  fillDelay: number
  approvalPoints: ApprovalPoint['type'][]
  maxRetries: number
  retryBaseDelay: number
  requireConfirmation: boolean
  humanizeTyping: boolean
}

export const DEFAULT_FORM_ENGINE_CONFIG: FormEngineConfig = {
  executionMode: 'manual_approval',
  fillDelay: 500,
  approvalPoints: ['before_submission'],
  maxRetries: 3,
  retryBaseDelay: 2000,
  requireConfirmation: true,
  humanizeTyping: false,
}

export interface ObservableEvent {
  type: string
  timestamp: string
  data: Record<string, unknown>
}
