export interface User {
  id: string
  email: string
  full_name: string | null
  is_active: boolean
  is_superuser?: boolean
  created_at: string
  updated_at: string
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
