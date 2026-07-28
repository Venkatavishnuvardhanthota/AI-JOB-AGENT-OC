import type { DownloadResult } from './types'
import { v4Service } from './utils'

const PREFIX = 'ajapp_brw_dl_'

function get<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch { return fallback }
}

function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

export const downloadService = {
  async download(url: string, sessionId: string, filename?: string): Promise<DownloadResult> {
    const id = v4Service.generate('dl')
    const now = new Date().toISOString()
    const ext = this.guessExtension(url)
    const name = filename || `download_${id}${ext}`

    const result: DownloadResult = {
      id,
      url,
      filename: name,
      path: `/downloads/${sessionId}/${name}`,
      mimeType: this.guessMimeType(ext),
      size: 0,
      createdAt: now,
      metadata: { sessionId },
    }

    const downloads = get<DownloadResult[]>(`${PREFIX}${sessionId}`, [])
    downloads.unshift(result)
    set(`${PREFIX}${sessionId}`, downloads.slice(0, 200))

    return result
  },

  getHistory(sessionId: string): DownloadResult[] {
    return get<DownloadResult[]>(`${PREFIX}${sessionId}`, [])
  },

  getById(sessionId: string, downloadId: string): DownloadResult | undefined {
    return this.getHistory(sessionId).find(d => d.id === downloadId)
  },

  delete(sessionId: string, downloadId: string): void {
    const downloads = this.getHistory(sessionId).filter(d => d.id !== downloadId)
    set(`${PREFIX}${sessionId}`, downloads)
  },

  clearAll(sessionId: string): void {
    set(`${PREFIX}${sessionId}`, [])
  },

  guessExtension(url: string): string {
    try {
      const pathname = new URL(url).pathname
      const match = pathname.match(/\.(\w+)$/)
      return match ? `.${match[1]}` : '.bin'
    } catch {
      return '.bin'
    }
  },

  guessMimeType(ext: string): string {
    const mimeMap: Record<string, string> = {
      '.pdf': 'application/pdf',
      '.doc': 'application/msword',
      '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      '.xls': 'application/vnd.ms-excel',
      '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      '.csv': 'text/csv',
      '.txt': 'text/plain',
      '.jpg': 'image/jpeg',
      '.jpeg': 'image/jpeg',
      '.png': 'image/png',
      '.zip': 'application/zip',
      '.json': 'application/json',
      '.xml': 'application/xml',
      '.html': 'text/html',
    }
    return mimeMap[ext.toLowerCase()] ?? 'application/octet-stream'
  },
}
