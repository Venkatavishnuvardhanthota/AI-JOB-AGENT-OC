import type { PaginationConfig } from './ats-types'

export interface PaginationParams {
  page: number
  pageSize: number
}

export interface PaginationResult<T> {
  items: T[]
  total: number
  hasMore: boolean
  cursor?: string
}

export function buildPaginationQuery(config: PaginationConfig, params: PaginationParams, cursor?: string): Record<string, string> {
  const q: Record<string, string> = {}
  const ps = Math.min(params.pageSize, config.maxPageSize)

  switch (config.style) {
    case 'page_per_page':
      if (config.pageParam) q[config.pageParam] = String(params.page)
      if (config.pageSizeParam) q[config.pageSizeParam] = String(ps)
      break
    case 'offset_limit':
      if (config.offsetParam) q[config.offsetParam] = String((params.page - 1) * ps)
      if (config.limitParam) q[config.limitParam] = String(ps)
      break
    case 'cursor':
      if (config.cursorParam && cursor) q[config.cursorParam] = cursor
      if (config.limitParam) q[config.limitParam] = String(ps)
      break
  }
  return q
}

export function extractPaginationResult<T>(response: unknown, config: PaginationConfig): PaginationResult<T> {
  const obj = response as Record<string, unknown>

  let total = 0
  if (config.totalPath) {
    let val: unknown = obj
    for (const key of config.totalPath) {
      val = (val as Record<string, unknown>)?.[key]
    }
    total = typeof val === 'number' ? val : 0
  }

  let hasMore = false
  if (config.hasMorePath) {
    let val: unknown = obj
    for (const key of config.hasMorePath) {
      val = (val as Record<string, unknown>)?.[key]
    }
    hasMore = typeof val === 'boolean' ? val : total > 0
  } else {
    hasMore = total > 0
  }

  let cursor: string | undefined
  if (config.cursorPath) {
    let val: unknown = obj
    for (const key of config.cursorPath) {
      val = (val as Record<string, unknown>)?.[key]
    }
    cursor = typeof val === 'string' ? val : undefined
  }

  let items: T[] = []
  if (config.itemsPath) {
    let val: unknown = obj
    for (const key of config.itemsPath) {
      val = (val as Record<string, unknown>)?.[key]
    }
    items = Array.isArray(val) ? (val as T[]) : []
  }

  return { items, total, hasMore, cursor }
}
