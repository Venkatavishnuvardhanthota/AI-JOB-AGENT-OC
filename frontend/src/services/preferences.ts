import type { ApplicationStatus } from '@/types'
import type { GroupBy } from './pipeline'

const PREFIX = 'ajapp_kanban_'

function get<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(PREFIX + key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

function set<T>(key: string, value: T): void {
  try {
    localStorage.setItem(PREFIX + key, JSON.stringify(value))
  } catch {}
}

export interface ColumnVisibility {
  [status: string]: boolean
}

export interface ColumnOrder {
  statuses: ApplicationStatus[]
}

export interface ColumnCollapse {
  [status: string]: boolean
}

export const preferenceService = {
  getColumnVisibility(): ColumnVisibility {
    return get<ColumnVisibility>('column_visibility', {})
  },

  setColumnVisibility(visibility: ColumnVisibility): void {
    set('column_visibility', visibility)
  },

  isColumnVisible(status: ApplicationStatus): boolean {
    const visibility = this.getColumnVisibility()
    return visibility[status] !== false
  },

  toggleColumnVisibility(status: ApplicationStatus): ColumnVisibility {
    const visibility = this.getColumnVisibility()
    visibility[status] = visibility[status] === false ? true : false
    this.setColumnVisibility(visibility)
    return visibility
  },

  getColumnOrder(): ApplicationStatus[] {
    return get<ApplicationStatus[]>('column_order', [])
  },

  setColumnOrder(order: ApplicationStatus[]): void {
    set('column_order', order)
  },

  getColumnCollapse(): ColumnCollapse {
    return get<ColumnCollapse>('column_collapse', {})
  },

  setColumnCollapse(collapse: ColumnCollapse): void {
    set('column_collapse', collapse)
  },

  isColumnCollapsed(status: ApplicationStatus): boolean {
    const collapse = this.getColumnCollapse()
    return collapse[status] === true
  },

  toggleColumnCollapse(status: ApplicationStatus): ColumnCollapse {
    const collapse = this.getColumnCollapse()
    collapse[status] = collapse[status] === true ? false : true
    this.setColumnCollapse(collapse)
    return collapse
  },

  getGroupBy(): GroupBy {
    return get<GroupBy>('group_by', 'none')
  },

  setGroupBy(groupBy: GroupBy): void {
    set('group_by', groupBy)
  },

  getViewMode(): 'board' | 'table' | 'cards' {
    return get<'board' | 'table' | 'cards'>('view_mode', 'board')
  },

  setViewMode(mode: 'board' | 'table' | 'cards'): void {
    set('view_mode', mode)
  },
}
