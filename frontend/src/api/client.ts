const API_BASE_URL = '/api/v1'
const SESSION_TIMEOUT_MS = 30 * 60 * 1000

let isRefreshing = false
let refreshPromise: Promise<boolean> | null = null
let sessionTimer: ReturnType<typeof setTimeout> | null = null
let onSessionExpired: (() => void) | null = null

type RefreshResult = { access_token: string; refresh_token?: string }

async function attemptRefresh(): Promise<boolean> {
  if (isRefreshing && refreshPromise) return refreshPromise
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) return false
  isRefreshing = true
  refreshPromise = (async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })
      if (!res.ok) throw new Error('Refresh failed')
      const json = await res.json()
      const data: RefreshResult = json?.data ?? json
      localStorage.setItem('access_token', data.access_token)
      if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token)
      resetSessionTimer()
      return true
    } catch {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('remembered_email')
      onSessionExpired?.()
      return false
    } finally {
      isRefreshing = false
      refreshPromise = null
    }
  })()
  return refreshPromise
}

function resetSessionTimer() {
  if (sessionTimer) clearTimeout(sessionTimer)
  sessionTimer = setTimeout(() => {
    onSessionExpired?.()
  }, SESSION_TIMEOUT_MS)
}

export function setOnSessionExpired(cb: () => void) {
  onSessionExpired = cb
}

export function clearSessionTimer() {
  if (sessionTimer) clearTimeout(sessionTimer)
  sessionTimer = null
}

export function touchSession() {
  resetSessionTimer()
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    if (response.status === 401) {
      const refreshed = await attemptRefresh()
      if (refreshed) throw new Error('__RETRY__')
      throw new Error('Session expired. Please sign in again.')
    }
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  if (response.status === 204) {
    return undefined as T
  }
  touchSession()
  return response.json()
}

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem('access_token')
  const headers: Record<string, string> = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

async function fetchWithRetry(url: string, options: RequestInit, retries = 1): Promise<Response> {
  const response = await fetch(url, options)
  if (response.status === 401 && retries > 0) {
    const refreshed = await attemptRefresh()
    if (refreshed) {
      const newHeaders = { ...options.headers as Record<string, string>, ...getAuthHeaders() }
      return fetchWithRetry(url, { ...options, headers: newHeaders }, 0)
    }
  }
  return response
}

export const api = {
  async get<T>(endpoint: string): Promise<T> {
    const response = await fetchWithRetry(`${API_BASE_URL}${endpoint}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    })
    return handleResponse<T>(response)
  },

  async post<T>(endpoint: string, body?: unknown): Promise<T> {
    const response = await fetchWithRetry(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: body ? JSON.stringify(body) : undefined,
    })
    return handleResponse<T>(response)
  },

  async put<T>(endpoint: string, body: unknown): Promise<T> {
    const response = await fetchWithRetry(`${API_BASE_URL}${endpoint}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify(body),
    })
    return handleResponse<T>(response)
  },

  async patch<T>(endpoint: string, body: unknown): Promise<T> {
    const response = await fetchWithRetry(`${API_BASE_URL}${endpoint}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify(body),
    })
    return handleResponse<T>(response)
  },

  async delete<T>(endpoint: string): Promise<T> {
    const response = await fetchWithRetry(`${API_BASE_URL}${endpoint}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    })
    return handleResponse<T>(response)
  },

  async uploadFile<T>(endpoint: string, file: File): Promise<T> {
    const formData = new FormData()
    formData.append('file', file)
    const headers = getAuthHeaders()
    delete headers['Content-Type']
    const response = await fetchWithRetry(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers,
      body: formData,
    })
    return handleResponse<T>(response)
  },
}

export const jobsApi = {
  search(params: { query: string; location?: string | null; remote_only?: boolean; sources?: string[] | null; salary_min?: number | null; salary_max?: number | null; job_type?: string | null; skills?: string[] | null; page?: number; page_size?: number }): Promise<{ items: any[]; total: number; page: number; page_size: number; total_pages: number }> {
    const q = new URLSearchParams()
    q.set('search', params.query)
    if (params.location) q.set('location', params.location)
    if (params.remote_only) q.set('remote_only', 'true')
    if (params.sources?.length) q.set('sources', params.sources.join(','))
    if (params.salary_min != null) q.set('salary_min', String(params.salary_min))
    if (params.salary_max != null) q.set('salary_max', String(params.salary_max))
    if (params.job_type) q.set('job_type', params.job_type)
    if (params.skills?.length) q.set('skills', params.skills.join(','))
    if (params.page != null) q.set('page', String(params.page))
    if (params.page_size != null) q.set('page_size', String(params.page_size))
    return api.get(`/jobs/search?${q}`)
  },

  list(params?: { page?: number; page_size?: number; source?: string; active_only?: boolean }): Promise<{ items: any[]; total: number; page: number; page_size: number; total_pages: number }> {
    const q = new URLSearchParams()
    if (params?.page != null) q.set('page', String(params.page))
    if (params?.page_size != null) q.set('page_size', String(params.page_size))
    if (params?.source) q.set('source', params.source)
    if (params?.active_only) q.set('active_only', 'true')
    const qs = q.toString()
    return api.get(`/jobs${qs ? `?${qs}` : ''}`)
  },

  get(id: string): Promise<any> {
    return api.get(`/jobs/${id}`)
  },

  update(id: string, data: { is_active?: boolean; viewed_at?: string | null; applied_at?: string | null }): Promise<any> {
    return api.patch(`/jobs/${id}`, data)
  },

  markApplied(id: string): Promise<any> {
    return api.patch(`/jobs/${id}`, { applied_at: new Date().toISOString() })
  },

  saved(params?: { page?: number; page_size?: number }): Promise<{ items: any[]; total: number; page: number; page_size: number; total_pages: number }> {
    const q = new URLSearchParams()
    if (params?.page != null) q.set('page', String(params.page))
    if (params?.page_size != null) q.set('page_size', String(params.page_size))
    const qs = q.toString()
    return api.get(`/jobs/saved${qs ? `?${qs}` : ''}`)
  },

  refresh(body: { query?: string; sources?: string[] }): Promise<{ task_id: string; status: string; error: string | null; created_at: string; completed_at: string | null }> {
    return api.post('/jobs/refresh', body)
  },

  taskStatus(taskId: string): Promise<{ task_id: string; status: string; error: string | null; created_at: string; completed_at: string | null }> {
    return api.get(`/jobs/refresh/status/${taskId}`)
  },

  stats(): Promise<{ total: number; viewed: number; applied: number; active: number; by_source: Record<string, number> }> {
    return api.get('/jobs/stats')
  },
}

export const matchingApi = {
  getConfig(): Promise<{ config: any; updated_at: string | null }> {
    return api.get('/matching/config')
  },

  updateConfig(config: any): Promise<{ config: any; updated_at: string | null }> {
    return api.put('/matching/config', config)
  },

  scoreJob(jobId: string): Promise<any> {
    return api.post(`/matching/jobs/${jobId}/score`)
  },

  scoreBatch(req: { job_ids: string[] }): Promise<{ scores: any[] }> {
    return api.post('/matching/jobs/batch-score', req)
  },

  explainScore(jobId: string): Promise<any[]> {
    return api.post(`/matching/jobs/${jobId}/explain`)
  },

  listScored(params?: { min_score?: number; page?: number; page_size?: number }): Promise<any[]> {
    const q = new URLSearchParams()
    if (params?.min_score != null) q.set('min_score', String(params.min_score))
    if (params?.page != null) q.set('page', String(params.page))
    if (params?.page_size != null) q.set('page_size', String(params.page_size))
    const qs = q.toString()
    return api.get(`/matching/jobs/scored${qs ? `?${qs}` : ''}`)
  },
}
