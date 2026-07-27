import { api } from '@/api/client'
import type { ActivityEntry } from '@/types'

function unwrap<T>(res: unknown): T {
  if (res && typeof res === 'object' && 'success' in res && (res as any).data !== undefined) {
    return (res as any).data as T
  }
  return res as T
}

export const activityService = {
  async list(applicationId: string): Promise<ActivityEntry[]> {
    const res = await api.get<ActivityEntry[]>(`/applications/${applicationId}/activity`)
    return unwrap<ActivityEntry[]>(res)
  },
}
