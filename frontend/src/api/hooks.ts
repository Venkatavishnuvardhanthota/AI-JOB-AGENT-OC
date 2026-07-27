import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, jobsApi } from './client'
import type {
  User, UserProfile, ScoringConfigResponse,
  BatchScoreRequest, BatchScoreResponse, ScoredJobResponse,
} from '@/types'

// ── Helpers ──
function unwrap<T>(res: any): T {
  if (res && typeof res === 'object' && 'success' in res && res.data !== undefined) {
    return res.data as T
  }
  return res as T
}

// ── Auth ──
export function useMe() {
  return useQuery({
    queryKey: ['me'],
    queryFn: () => api.get<User>('/auth/me').then(unwrap<User>),
    retry: false,
  })
}

export function useUpdateUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { first_name?: string; last_name?: string }) =>
      api.patch('/auth/me', data).then(unwrap<User>),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['me'] }),
  })
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (data: { current_password: string; new_password: string }) =>
      api.post('/auth/change-password', data),
  })
}

// ── Profile ──
export function useProfile() {
  return useQuery({
    queryKey: ['profile'],
    queryFn: () => api.get<UserProfile>('/profile').then(unwrap<UserProfile>),
  })
}

export function useProfileCompleteness() {
  return useQuery({
    queryKey: ['profile', 'completeness'],
    queryFn: () => api.get('/profile/completeness').then(unwrap),
  })
}

export function useUpdateProfile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: any) => api.patch('/profile', data).then(unwrap<UserProfile>),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['profile'] }); qc.invalidateQueries({ queryKey: ['profile', 'completeness'] }) },
  })
}

export function useProfileSection<T>(section: string) {
  return useQuery({
    queryKey: ['profile', section],
    queryFn: () => api.get<T[]>(`/profile/${section}`).then(unwrap<T[]>),
  })
}

export function useCreateProfileSection<T>(section: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: any) => api.post<T>(`/profile/${section}`, data).then(unwrap<T>),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['profile', section] }),
  })
}

export function useUpdateProfileSection<T>(section: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      api.patch<T>(`/profile/${section}/${id}`, data).then(unwrap<T>),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['profile', section] }),
  })
}

export function useDeleteProfileSection(section: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.delete(`/profile/${section}/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['profile', section] }),
  })
}

// ── Resume Sections ──
export function useResumeSections(resumeId: string) {
  return useQuery({
    queryKey: ['resumes', resumeId, 'sections'],
    queryFn: () => api.get<any[]>(`/resumes/${resumeId}/sections`).then(unwrap),
    enabled: !!resumeId,
  })
}

export function useCreateResumeSection(resumeId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: any) => api.post(`/resumes/${resumeId}/sections`, data).then(unwrap),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['resumes', resumeId, 'sections'] }),
  })
}

export function useUpdateResumeSection(resumeId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ sectionId, data }: { sectionId: string; data: any }) =>
      api.patch(`/resumes/${resumeId}/sections/${sectionId}`, data).then(unwrap),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['resumes', resumeId, 'sections'] }),
  })
}

export function useDeleteResumeSection(resumeId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (sectionId: string) => api.delete(`/resumes/${resumeId}/sections/${sectionId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['resumes', resumeId, 'sections'] }),
  })
}

// ── Resumes ──
export function useResumes(archived?: boolean) {
  return useQuery({
    queryKey: ['resumes', archived],
    queryFn: () => {
      const params = archived != null ? `?archived=${archived}` : ''
      return api.get<any[]>(`/resumes${params}`).then(unwrap)
    },
  })
}

export function useResume(id: string) {
  return useQuery({
    queryKey: ['resumes', id],
    queryFn: () => api.get<any>(`/resumes/${id}`).then(unwrap),
    enabled: !!id,
  })
}

export function useCreateResume() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: any) => api.post('/resumes', data).then(unwrap),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['resumes'] }),
  })
}

export function useUpdateResume() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      api.patch(`/resumes/${id}`, data).then(unwrap),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['resumes'] }); },
  })
}

export function useDeleteResume() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.delete(`/resumes/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['resumes'] }),
  })
}

export function useArchiveResume() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.post(`/resumes/${id}/archive`, undefined).then(unwrap),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['resumes'] }),
  })
}

export function useRestoreResume() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.post(`/resumes/${id}/restore`, undefined).then(unwrap),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['resumes'] }),
  })
}

export function useResumeTemplates() {
  return useQuery({
    queryKey: ['resume-templates'],
    queryFn: () => api.get<any[]>('/resumes/templates').then(unwrap),
  })
}

// ── Jobs ──
export function useJobSearch(params: { query: string; location?: string | null; remote_only?: boolean; sources?: string[] | null; salary_min?: number | null; salary_max?: number | null; job_type?: string | null; skills?: string[] | null; page?: number; page_size?: number }) {
  return useQuery({
    queryKey: ['jobs', 'search', params],
    queryFn: () => jobsApi.search(params).then((r: any) => ('success' in r ? r : { items: r.items || [], total: r.total || 0, page: params.page || 1, page_size: params.page_size || 20, total_pages: r.total_pages || 1 })),
    enabled: !!params.query,
  })
}

export function useJobs(params?: Record<string, any>) {
  return useQuery({
    queryKey: ['jobs', 'list', params],
    queryFn: () => jobsApi.list(params).then((r: any) => r),
  })
}

export function useJob(id: string) {
  return useQuery({
    queryKey: ['jobs', id],
    queryFn: () => api.get<any>(`/jobs/${id}`).then(unwrap),
    enabled: !!id,
  })
}

export function useJobMatch(id: string) {
  return useQuery({
    queryKey: ['jobs', id, 'match'],
    queryFn: () => api.get<any>(`/jobs/${id}/match`).then(unwrap),
    enabled: !!id,
  })
}

export function useJobCompany(id: string) {
  return useQuery({
    queryKey: ['jobs', id, 'company'],
    queryFn: () => api.get<any>(`/jobs/${id}/company`).then(unwrap),
    enabled: !!id,
  })
}

export function useJobStats() {
  return useQuery({
    queryKey: ['jobs', 'stats'],
    queryFn: () => jobsApi.stats(),
  })
}

export function useSavedJobs(params?: { page?: number; page_size?: number }) {
  return useQuery({
    queryKey: ['jobs', 'saved', params],
    queryFn: () => jobsApi.saved(params),
  })
}

export function useJobProviders() {
  return useQuery({
    queryKey: ['job-providers'],
    queryFn: () => api.get<any[]>('/jobs/providers').then(unwrap),
  })
}

export function useRefreshJobs() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { query?: string; sources?: string[] }) =>
      jobsApi.refresh(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['jobs'] }),
  })
}

// ── Applications ──
export function useApplications(params?: { status?: string; page?: number; page_size?: number }) {
  const q = new URLSearchParams()
  if (params?.status) q.set('status', params.status)
  if (params?.page) q.set('page', String(params.page))
  if (params?.page_size) q.set('page_size', String(params.page_size))
  const qs = q.toString()
  return useQuery({
    queryKey: ['applications', params],
    queryFn: () => api.get(`/applications${qs ? `?${qs}` : ''}`).then(unwrap),
  })
}

export function useApplication(id: string) {
  return useQuery({
    queryKey: ['applications', id],
    queryFn: () => api.get<any>(`/applications/${id}`).then(unwrap),
    enabled: !!id,
  })
}

export function usePrepareApplication() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { job_id: string; resume_id?: string; generate_cover_letter?: boolean; generate_ai_answers?: boolean }) =>
      api.post('/applications/prepare', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['applications'] }),
  })
}

export function useSubmitApplication() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.post(`/applications/${id}/submit`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['applications'] }),
  })
}

export function useCancelApplication() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.post(`/applications/${id}/cancel`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['applications'] }),
  })
}

export function useApplicationTimeline(id: string) {
  return useQuery({
    queryKey: ['applications', id, 'timeline'],
    queryFn: () => api.get<any[]>(`/applications/${id}/timeline`).then(unwrap),
    enabled: !!id,
  })
}

// ── Matching ──
export function useMatchingConfig() {
  return useQuery({
    queryKey: ['matching-config'],
    queryFn: () => api.get<ScoringConfigResponse>('/matching/config').then(unwrap),
  })
}

export function useScoreJob() {
  return useMutation({
    mutationFn: (jobId: string) => api.post(`/matching/jobs/${jobId}/score`),
  })
}

export function useScoreBatch() {
  return useMutation({
    mutationFn: (req: BatchScoreRequest) => api.post<BatchScoreResponse>('/matching/jobs/batch-score', req).then(unwrap),
  })
}

export function useScoredJobs(params?: { min_score?: number; page?: number; page_size?: number }) {
  const q = new URLSearchParams()
  if (params?.min_score != null) q.set('min_score', String(params.min_score))
  if (params?.page != null) q.set('page', String(params.page))
  if (params?.page_size != null) q.set('page_size', String(params.page_size))
  const qs = q.toString()
  return useQuery({
    queryKey: ['scored-jobs', params],
    queryFn: () => api.get<ScoredJobResponse[]>(`/matching/jobs/scored${qs ? `?${qs}` : ''}`).then(unwrap),
  })
}

// ── Cover Letters (via profile) ──
export function useCoverLetters() {
  return useQuery({
    queryKey: ['cover-letters'],
    queryFn: () => api.get<any[]>('/profile/cover-letters').catch(() => []),
  })
}

// ── Resume Upload / Generate / Duplicate / Optimize / Compare / Download ──
export function useUploadResume() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (formData: FormData) => {
      const token = localStorage.getItem('access_token')
      return fetch('/api/v1/resumes/upload', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      }).then(r => r.json()).then(unwrap)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['resumes'] }),
  })
}

export function useGenerateResume() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: any) => api.post('/resumes/generate', data).then(unwrap),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['resumes'] }),
  })
}

export function useDuplicateResume() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data?: any }) =>
      api.post(`/resumes/${id}/duplicate`, data || {}).then(unwrap),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['resumes'] }),
  })
}

export function useOptimizeResume() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      api.post(`/resumes/${id}/optimize`, data).then(unwrap),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['resumes'] }); },
  })
}

export function useCompareResumes() {
  return useMutation({
    mutationFn: (data: any) => api.post('/resumes/compare', data).then(unwrap),
  })
}

export function useDownloadResume() {
  return useMutation({
    mutationFn: async ({ id, format }: { id: string; format?: string }) => {
      const token = localStorage.getItem('access_token')
      const fmt = format || 'pdf'
      const res = await fetch(`/api/v1/resumes/${id}/download/${fmt}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Download failed')
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = `resume-${id}.${fmt}`
      document.body.appendChild(a); a.click()
      document.body.removeChild(a); window.URL.revokeObjectURL(url)
      return res
    },
  })
}
