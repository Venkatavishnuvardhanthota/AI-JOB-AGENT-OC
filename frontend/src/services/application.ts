import { api } from '@/api/client'
import type {
  Application,
  ApplicationListResponse,
  ApplicationCreateRequest,
  ApplicationUpdateRequest,
  ApplicationStats,
  ApplicationSearchParams,
  ApplicationStatus,
  ApplicationPriority,
} from '@/types'

function unwrap<T>(res: unknown): T {
  if (res && typeof res === 'object' && 'success' in res && (res as any).data !== undefined) {
    return (res as any).data as T
  }
  return res as T
}

function buildSearchQuery(params: ApplicationSearchParams): string {
  const q = new URLSearchParams()
  if (params.search) q.set('search', params.search)
  if (params.status) {
    if (Array.isArray(params.status)) q.set('status', params.status.join(','))
    else q.set('status', params.status)
  }
  if (params.priority) {
    if (Array.isArray(params.priority)) q.set('priority', params.priority.join(','))
    else q.set('priority', params.priority)
  }
  if (params.company) q.set('company', params.company)
  if (params.location) q.set('location', params.location)
  if (params.recruiter) q.set('recruiter', params.recruiter)
  if (params.source) q.set('source', params.source)
  if (params.salary_min != null) q.set('salary_min', String(params.salary_min))
  if (params.salary_max != null) q.set('salary_max', String(params.salary_max))
  if (params.skills?.length) q.set('skills', params.skills.join(','))
  if (params.date_from) q.set('date_from', params.date_from)
  if (params.date_to) q.set('date_to', params.date_to)
  if (params.sort_by) q.set('sort_by', params.sort_by)
  if (params.sort_order) q.set('sort_order', params.sort_order)
  if (params.page != null) q.set('page', String(params.page))
  if (params.page_size != null) q.set('page_size', String(params.page_size))
  return q.toString()
}

export const applicationService = {
  async list(params?: ApplicationSearchParams): Promise<ApplicationListResponse> {
    const qs = params ? buildSearchQuery(params) : ''
    const res = await api.get<ApplicationListResponse>(`/applications${qs ? `?${qs}` : ''}`)
    return unwrap<ApplicationListResponse>(res)
  },

  async get(id: string): Promise<Application> {
    const res = await api.get<Application>(`/applications/${id}`)
    return unwrap<Application>(res)
  },

  async create(data: ApplicationCreateRequest): Promise<Application> {
    const res = await api.post<Application>('/applications', data)
    return unwrap<Application>(res)
  },

  async update(id: string, data: ApplicationUpdateRequest): Promise<Application> {
    const res = await api.patch<Application>(`/applications/${id}`, data)
    return unwrap<Application>(res)
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/applications/${id}`)
  },

  async getStats(): Promise<ApplicationStats> {
    const res = await api.get<ApplicationStats>('/applications/stats')
    return unwrap<ApplicationStats>(res)
  },

  async updateStatus(id: string, status: ApplicationStatus): Promise<Application> {
    return this.update(id, { status })
  },

  async updatePriority(id: string, priority: ApplicationPriority): Promise<Application> {
    return this.update(id, { priority })
  },

  async bulkAction(application_ids: string[], action: string, value?: string): Promise<void> {
    await api.post('/applications/bulk', { application_ids, action, value })
  },
}
