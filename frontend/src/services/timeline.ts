import { api } from '@/api/client'
import type { TimelineEntry } from '@/types'

function unwrap<T>(res: unknown): T {
  if (res && typeof res === 'object' && 'success' in res && (res as any).data !== undefined) {
    return (res as any).data as T
  }
  return res as T
}

export const timelineService = {
  async list(applicationId: string): Promise<TimelineEntry[]> {
    const res = await api.get<TimelineEntry[]>(`/applications/${applicationId}/timeline`)
    return unwrap<TimelineEntry[]>(res)
  },
}
