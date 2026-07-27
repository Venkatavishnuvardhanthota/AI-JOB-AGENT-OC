import { api } from '@/api/client'
import type { ApplicationNote, NoteCreateRequest, NoteUpdateRequest } from '@/types'

function unwrap<T>(res: unknown): T {
  if (res && typeof res === 'object' && 'success' in res && (res as any).data !== undefined) {
    return (res as any).data as T
  }
  return res as T
}

export const noteService = {
  async list(applicationId: string): Promise<ApplicationNote[]> {
    const res = await api.get<ApplicationNote[]>(`/applications/${applicationId}/notes`)
    return unwrap<ApplicationNote[]>(res)
  },

  async create(applicationId: string, data: NoteCreateRequest): Promise<ApplicationNote> {
    const res = await api.post<ApplicationNote>(`/applications/${applicationId}/notes`, data)
    return unwrap<ApplicationNote>(res)
  },

  async update(noteId: string, data: NoteUpdateRequest): Promise<ApplicationNote> {
    const res = await api.patch<ApplicationNote>(`/notes/${noteId}`, data)
    return unwrap<ApplicationNote>(res)
  },

  async delete(noteId: string): Promise<void> {
    await api.delete(`/notes/${noteId}`)
  },
}
