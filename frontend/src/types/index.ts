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

export interface UserProfile {
  id: string
  user_id: string
  phone: string | null
  headline: string | null
  bio: string | null
  location: string | null
  salary_expectation_min: number | null
  salary_expectation_max: number | null
  salary_currency: string | null
  portfolio_url: string | null
  linkedin_url: string | null
  github_url: string | null
  resume_file: string | null
  created_at: string
  updated_at: string
}

export interface Education {
  id: string
  user_id: string
  institution: string
  degree: string
  field_of_study: string | null
  start_date: string | null
  end_date: string | null
  gpa: number | null
  description: string | null
  created_at: string
  updated_at: string
}

export interface Experience {
  id: string
  user_id: string
  company: string
  title: string
  location: string | null
  start_date: string | null
  end_date: string | null
  is_current: boolean
  description: string | null
  company_url: string | null
  created_at: string
  updated_at: string
}

export interface Project {
  id: string
  user_id: string
  name: string
  description: string | null
  url: string | null
  github_url: string | null
  start_date: string | null
  end_date: string | null
  is_current: boolean
  created_at: string
  updated_at: string
}

export interface Skill {
  id: string
  user_id: string
  name: string
  category: string | null
  proficiency: number | null
  created_at: string
  updated_at: string
}

export interface Certification {
  id: string
  user_id: string
  name: string
  issuer: string | null
  issue_date: string | null
  expiry_date: string | null
  credential_id: string | null
  credential_url: string | null
  file_url: string | null
  created_at: string
  updated_at: string
}

export interface Language {
  id: string
  user_id: string
  name: string
  proficiency: string
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
