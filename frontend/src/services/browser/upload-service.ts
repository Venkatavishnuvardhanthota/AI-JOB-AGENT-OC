import type { UploadResult } from './types'
import { v4Service } from './utils'

const PREFIX = 'ajapp_brw_ul_'

function get<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch { return fallback }
}

function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

export const uploadService = {
  async upload(
    file: File,
    targetUrl: string,
    sessionId: string,
    fieldName: string = 'file'
  ): Promise<UploadResult> {
    const id = v4Service.generate('ul')
    const fileSize = file.size
    const mimeType = file.type || 'application/octet-stream'

    const result: UploadResult = {
      id,
      filename: file.name,
      fileSize,
      mimeType,
      fieldName,
      targetUrl,
      status: 'uploading',
      createdAt: new Date().toISOString(),
      metadata: { sessionId, lastModified: file.lastModified },
    }

    this.logUpload(sessionId, result)
    result.status = 'uploaded'
    this.logUpload(sessionId, result)

    return result
  },

  async uploadMultiple(
    files: File[],
    targetUrl: string,
    sessionId: string,
    fieldName: string = 'files'
  ): Promise<UploadResult[]> {
    return Promise.all(files.map(f => this.upload(f, targetUrl, sessionId, fieldName)))
  },

  logUpload(sessionId: string, result: UploadResult): void {
    const uploads = get<UploadResult[]>(`${PREFIX}${sessionId}`, [])
    const idx = uploads.findIndex(u => u.id === result.id)
    if (idx !== -1) uploads[idx] = result
    else uploads.unshift(result)
    set(`${PREFIX}${sessionId}`, uploads.slice(0, 100))
  },

  getUploads(sessionId: string): UploadResult[] {
    return get<UploadResult[]>(`${PREFIX}${sessionId}`, [])
  },

  getById(sessionId: string, uploadId: string): UploadResult | undefined {
    return this.getUploads(sessionId).find(u => u.id === uploadId)
  },

  clearHistory(sessionId: string): void {
    set(`${PREFIX}${sessionId}`, [])
  },
}
