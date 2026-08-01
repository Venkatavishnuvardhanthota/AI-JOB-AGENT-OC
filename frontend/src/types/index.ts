export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  is_active: boolean
  is_superuser?: boolean
  is_verified?: boolean
  created_at: string
  updated_at?: string
  last_login: string | null
}

export interface UserListResponse {
  items: User[]
  total: number
  page: number
  page_size: number
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name?: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export type SalaryPreference = 'paid_only' | 'paid_preferred' | 'unpaid_acceptable'

export interface JobPreference {
  id: string
  preferred_titles: string[]
  preferred_locations: string[]
  employment_types: string[]
  work_modes: string[]
  minimum_salary: number | null
  preferred_currency: string | null
  created_at: string
  updated_at: string
}

export interface UserProfile {
  id: string
  headline: string | null
  professional_summary: string | null
  total_years_experience: number | null
  current_role: string | null
  desired_role: string | null
  employment_status: string | null
  current_salary: number | null
  expected_salary: number | null
  salary_preference: SalaryPreference | null
  willing_to_relocate: boolean | null
  visa_sponsorship_requirement: boolean | null
  notice_period: string | null
  portfolio_url: string | null
  linkedin_url: string | null
  github_url: string | null
  website_url: string | null
  profile_completeness: number | null
  education: Education[]
  experience: Experience[]
  projects: Project[]
  skills: Skill[]
  certifications: Certification[]
  languages: Language[]
  social_links: SocialLink[]
  achievements: Achievement[]
  preferences: JobPreference | null
  created_at: string
  updated_at: string
}

export interface ProfileCompleteness {
  percentage: number
  breakdown: Record<string, number>
  missing_sections: string[]
}

export interface Education {
  id: string
  profile_id: string
  institution: string
  degree: string
  field_of_study: string | null
  location: string | null
  start_date: string | null
  end_date: string | null
  currently_studying: boolean | null
  cgpa: string | null
  created_at: string
  updated_at: string
}

export interface Experience {
  id: string
  profile_id: string
  company: string
  title: string
  location: string | null
  employment_type: string | null
  start_date: string | null
  end_date: string | null
  currently_working: boolean | null
  responsibilities: string[] | null
  achievements: string[] | null
  technologies_used: string[] | null
  description: string | null
  created_at: string
  updated_at: string
}

export interface Project {
  id: string
  profile_id: string
  name: string
  description: string | null
  technologies: string[] | null
  github_url: string | null
  demo_url: string | null
  live_url: string | null
  start_date: string | null
  end_date: string | null
  created_at: string
  updated_at: string
}

export interface Skill {
  id: string
  profile_id: string
  name: string
  category: string | null
  proficiency: string | null
  years_experience: number | null
  skill_level: string | null
  display_order: number | null
  created_at: string
  updated_at: string
}

export interface Certification {
  id: string
  profile_id: string
  name: string
  issuer: string | null
  credential_id: string | null
  issue_date: string | null
  expiration_date: string | null
  credential_url: string | null
  created_at: string
  updated_at: string
}

export interface Language {
  id: string
  profile_id: string
  language: string
  proficiency: string | null
  created_at: string
  updated_at: string
}

export type SocialLinkPlatform = 'linkedin' | 'github' | 'portfolio' | 'website' | 'other'

export interface SocialLink {
  id: string
  profile_id: string
  platform: SocialLinkPlatform
  url: string
  display_order: number | null
  title: string
  created_at: string
  updated_at: string
}

export interface Achievement {
  id: string
  profile_id: string
  title: string
  organization: string | null
  achievement_type: string | null
  date: string | null
  description: string | null
  url: string | null
  display_order: number | null
  created_at: string
  updated_at: string
}

export interface BlacklistedCompany {
  id: string
  user_id: string
  company_name: string
  reason: string | null
  created_at: string
  updated_at: string
}

export interface JobPosting {
  id: string
  title: string
  company_name: string
  company_url: string | null
  company_logo_url: string | null
  location: string | null
  description: string | null
  url: string | null
  source: string
  source_job_id: string | null
  salary_min: number | null
  salary_max: number | null
  salary_currency: string | null
  salary_period: string | null
  posted_at: string | null
  job_type: string | null
  remote: boolean
  apply_url: string | null
  skills: string[]
  requirements: string[]
  benefits: string[]
  categories: string[]
  content_hash: string
  is_active: boolean
  viewed_at: string | null
  applied_at: string | null
  created_at: string
  updated_at: string
}

export interface JobSearchRequest {
  query: string
  location?: string | null
  remote_only?: boolean
  sources?: string[] | null
  salary_min?: number | null
  salary_max?: number | null
  job_type?: string | null
  skills?: string[] | null
  page?: number
  page_size?: number
}

export interface JobSearchResponse {
  items: JobPosting[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface JobSearchResult {
  jobs: JobPosting[]
  providers: { name: string; enabled: boolean; jobs_found: number | null; error: string | null }[]
  total_new: number
  duplicates_removed: number
}

export interface JobUpdate {
  is_active?: boolean
  viewed_at?: string | null
  applied_at?: string | null
}

export interface JobStats {
  total: number
  viewed: number
  applied: number
  active: number
  by_source: Record<string, number>
}

export interface TaskStatusResponse {
  task_id: string
  status: string
  error: string | null
  created_at: string
  completed_at: string | null
}

export interface SkillScore {
  matched: string[]
  missing: string[]
  total_user: number
  total_job: number
  score: number
}

export interface KeywordScore {
  extracted: string[]
  matched: string[]
  total: number
  score: number
}

export interface ExperienceScore {
  user_years: number
  required_years: number | null
  has_relevant: boolean
  relevant_titles: string[]
  score: number
}

export interface EducationScore {
  user_level: string
  required_level: string | null
  user_field: string | null
  required_field: string | null
  level_match: boolean
  field_match: boolean
  score: number
}

export interface CompanyScore {
  company_name: string
  is_blacklisted: boolean
  has_connections: boolean
  score: number
}

export interface ScoreExplanation {
  category: string
  score: number
  weight: number
  details: string
}

export interface MatchScore {
  overall: number
  skill: SkillScore
  keyword: KeywordScore
  experience: ExperienceScore
  education: EducationScore
  company: CompanyScore
  explanations: ScoreExplanation[]
  scored_at: string | null
  job_id: string | null
}

export interface ScoringWeights {
  skill: number
  keyword: number
  experience: number
  education: number
  company: number
}

export interface ScoringConfig {
  weights: ScoringWeights
  skill_threshold: number
  keyword_threshold: number
  experience_threshold: number
  education_threshold: number
  overall_threshold: number
  boost_exact_title_match: boolean
  boost_current_company: boolean
  penalty_blacklisted: boolean
}

export interface ScoringConfigResponse {
  config: ScoringConfig
  updated_at: string | null
}

export interface BatchScoreRequest {
  job_ids: string[]
}

export interface BatchScoreResponse {
  scores: MatchScore[]
}

export interface ScoredJobResponse {
  id: string
  title: string
  company_name: string
  location: string | null
  source: string
  salary_min: number | null
  salary_max: number | null
  salary_currency: string | null
  job_type: string | null
  remote: boolean
  posted_at: string | null
  skills: string[]
  is_active: boolean
  match_score: number
  match_details: ScoreExplanation | null
}

export type ApplicationStatus =
  | 'saved'
  | 'preparing'
  | 'ready_to_apply'
  | 'applied'
  | 'application_viewed'
  | 'assessment'
  | 'technical_interview'
  | 'hr_interview'
  | 'final_interview'
  | 'offer'
  | 'negotiation'
  | 'accepted'
  | 'rejected'
  | 'withdrawn'
  | 'archived'

export type ApplicationPriority = 'critical' | 'high' | 'medium' | 'low'

export interface Application {
  id: string
  user_id: string
  job_id: string
  job_title: string
  company_name: string
  company_id?: string
  resume_id?: string
  cover_letter_id?: string
  resume_strategy?: string
  original_resume_id?: string
  generated_resume_id?: string
  generated?: boolean
  tailored?: boolean
  generation_timestamp?: string
  status: ApplicationStatus
  priority: ApplicationPriority
  applied_date?: string
  deadline?: string
  salary?: string
  location?: string
  work_type?: string
  source?: string
  recruiter?: string
  referral?: boolean
  notes?: ApplicationNote[]
  created_at: string
  updated_at: string
}

export interface ApplicationListResponse {
  items: Application[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ApplicationStats {
  total: number
  applied_this_week: number
  interviews: number
  offers: number
  acceptance_rate: number
  response_rate: number
  upcoming_deadlines: number
  recent_activity: number
  by_status: Record<string, number>
  by_priority: Record<string, number>
}

export interface ApplicationCreateRequest {
  job_id: string
  resume_id?: string
  cover_letter_id?: string
  status?: ApplicationStatus
  priority?: ApplicationPriority
  notes?: string
}

export interface ApplicationUpdateRequest {
  status?: ApplicationStatus
  priority?: ApplicationPriority
  applied_date?: string
  deadline?: string
  salary?: string
  location?: string
  work_type?: string
  source?: string
  recruiter?: string
  referral?: boolean
  resume_id?: string
  cover_letter_id?: string
}

export interface ApplicationSearchParams {
  search?: string
  status?: ApplicationStatus | ApplicationStatus[]
  priority?: ApplicationPriority | ApplicationPriority[]
  company?: string
  location?: string
  recruiter?: string
  source?: string
  salary_min?: number
  salary_max?: number
  skills?: string[]
  date_from?: string
  date_to?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}

export interface TimelineEntry {
  id: string
  application_id: string
  event_type: string
  description: string
  metadata?: Record<string, unknown>
  created_at: string
}

export interface ApplicationNote {
  id: string
  application_id: string
  title: string
  content: string
  author: string
  created_at: string
  updated_at: string
}

export interface NoteCreateRequest {
  title: string
  content: string
}

export interface NoteUpdateRequest {
  title?: string
  content?: string
}

export interface ActivityEntry {
  id: string
  application_id: string
  action: string
  field?: string
  old_value?: string
  new_value?: string
  created_at: string
}

export interface BulkActionRequest {
  application_ids: string[]
  action: 'archive' | 'delete' | 'status_change' | 'priority_change'
  value?: string
}

export interface DocumentInfo {
  id: string
  type: 'resume' | 'cover_letter' | 'attachment'
  name: string
  version?: string
  created_at: string
  updated_at: string
  file_url?: string
}

// ── AI Types ──
export interface CapabilityInfo {
  chat: boolean
  streaming: boolean
  vision: boolean
  json_mode: boolean
  embeddings: boolean
  reasoning: boolean
  function_calling: boolean
  tool_calling: boolean
  system_prompt_support: boolean
  structured_output: boolean
}

export interface AIModel {
  id: string
  name: string
  provider: string
  description?: string
  max_tokens?: number
  supports_streaming: boolean
  supports_function_calling: boolean
  supports_vision: boolean
  supports_json_mode: boolean
  supports_reasoning: boolean
}

export interface AIProvider {
  name: string
  display_name: string
  description?: string
  version?: string
  is_available: boolean
  supports_streaming: boolean
  configured: boolean
  is_default: boolean
  capabilities?: CapabilityInfo
  models: AIModel[]
  error?: string
}

export interface ProviderStatus {
  name: string
  display_name: string
  configured: boolean
  enabled: boolean
  healthy?: boolean
  connected?: boolean
  is_default: boolean
  available: boolean
  implementation_status: string
  capabilities: CapabilityInfo
  models: AIModel[]
  error?: string
}

export interface HealthCheckResult {
  provider: string
  model?: string
  healthy: boolean
  connected?: boolean
  latency_ms?: number
  available: boolean
  configured: boolean
  is_default: boolean
  error?: string
}

export interface AIHealthResponse {
  status: 'healthy' | 'degraded'
  overall_healthy: boolean
  providers: HealthCheckResult[]
}

export interface AIConfigData {
  default_provider: string
  default_model: string
  fallback_model?: string
  fallback_provider?: string
  max_retries: number
  retry_delay_seconds: number
  timeout_seconds: number
  temperature: number
  max_tokens: number
  enabled_providers: string[]
  streaming_enabled: boolean
}

export interface AIUpdateConfigData {
  default_provider?: string
  default_model?: string
  temperature?: number
  max_tokens?: number
  timeout_seconds?: number
  max_retries?: number
  retry_delay_seconds?: number
  streaming_enabled?: boolean
  enabled_providers?: string[]
  openrouter_api_key?: string
  openai_api_key?: string
  anthropic_api_key?: string
  gemini_api_key?: string
  ollama_base_url?: string
}

export interface AIProviderTestResult {
  provider: string
  healthy: boolean
  connected?: boolean
  latency_ms?: number
  model?: string
  error?: string
}

export interface PromptTemplateInfo {
  name: string
  description?: string
  version?: string
  variables: string[]
  has_system_prompt: boolean
}

// ── Resume Strategy ──

export type ResumeStrategyOption = 'use_existing' | 'tailor' | 'generate' | 'ask'
export type SaveGeneratedResumesOption = 'never' | 'submitted_only' | 'every'

export interface ResumeStrategySettingsData {
  resume_strategy: ResumeStrategyOption
  save_generated_resumes: SaveGeneratedResumesOption
}

export interface ResumeStrategySettingsUpdateData {
  resume_strategy?: ResumeStrategyOption
  save_generated_resumes?: SaveGeneratedResumesOption
}

export interface ResumeSelectionScoreData {
  resume_id: string
  title: string | null
  skill_overlap: number
  keyword_overlap: number
  role_alignment: number
  ats_compatibility: number
  overall: number
  selected: boolean
}

export interface ResumeStrategyPreviewData {
  recommended_strategy: ResumeStrategyOption
  selected_resume_id: string | null
  selected_resume_title: string | null
  scores: ResumeSelectionScoreData[]
  generated_resume_id: string | null
  generated_resume_title: string | null
  reused_generated: boolean
  rationale: string
}

export interface ResumeStrategyPrepareData {
  application_id: string | null
  status: string | null
  needs_choice: boolean
  strategy: ResumeStrategyOption
  selected_resume_id: string | null
  selected_resume_title: string | null
  generated_resume_id: string | null
  generated_resume_title: string | null
  cover_letter_id: string | null
  reused_generated: boolean
  reason: string | null
  created_at: string | null
  job_id?: string | null
  options?: ResumeStrategyOption[]
}

export interface APISuccessResponse<T> {
  success: true
  data: T
}
