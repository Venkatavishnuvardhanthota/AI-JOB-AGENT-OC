import type { QueueEntry, QueueType, WorkflowStage } from './types'
import { nowISO } from './utils'

const PREFIX = 'ajapp_ork_q_'

function get<T>(key: string, fallback: T): T {
  try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback } catch { return fallback }
}
function set<T>(key: string, value: T): void { try { localStorage.setItem(key, JSON.stringify(value)) } catch {} }

export const workflowQueueService = {
  enqueue(workflowId: string, queueType: QueueType, priority: number, stage: WorkflowStage, reason: string | null = null): QueueEntry {
    const entry: QueueEntry = { workflowId, queueType, priority, stage, enqueuedAt: nowISO(), retryCount: 0, reason }
    const queue = this.getQueue(queueType)
    queue.push(entry)
    set(`${PREFIX}${queueType}`, queue.sort((a, b) => b.priority - a.priority || a.enqueuedAt.localeCompare(b.enqueuedAt)))
    return entry
  },

  dequeue(queueType: QueueType): QueueEntry | null {
    const queue = this.getQueue(queueType)
    if (queue.length === 0) return null
    const entry = queue.shift()!
    set(`${PREFIX}${queueType}`, queue)
    return entry
  },

  getQueue(queueType: QueueType): QueueEntry[] {
    return get<QueueEntry[]>(`${PREFIX}${queueType}`, [])
  },

  peek(queueType: QueueType): QueueEntry | null {
    const queue = this.getQueue(queueType)
    return queue.length > 0 ? queue[0] : null
  },

  remove(workflowId: string, queueType: QueueType): void {
    const queue = this.getQueue(queueType).filter(e => e.workflowId !== workflowId)
    set(`${PREFIX}${queueType}`, queue)
  },

  moveTo(workflowId: string, from: QueueType, to: QueueType, reason: string | null = null): void {
    const entry = this.getQueue(from).find(e => e.workflowId === workflowId)
    if (entry) {
      this.remove(workflowId, from)
      this.enqueue(workflowId, to, entry.priority, entry.stage, reason)
    }
  },

  updatePriority(workflowId: string, queueType: QueueType, priority: number): void {
    const queue = this.getQueue(queueType)
    const entry = queue.find(e => e.workflowId === workflowId)
    if (entry) {
      entry.priority = priority
      set(`${PREFIX}${queueType}`, queue.sort((a, b) => b.priority - a.priority || a.enqueuedAt.localeCompare(b.enqueuedAt)))
    }
  },

  incrementRetry(workflowId: string): void {
    for (const type of ['priority', 'retry'] as QueueType[]) {
      const entry = this.getQueue(type).find(e => e.workflowId === workflowId)
      if (entry) { entry.retryCount++; set(`${PREFIX}${type}`, this.getQueue(type)); break }
    }
  },

  size(queueType: QueueType): number {
    return this.getQueue(queueType).length
  },

  totalSize(): { [key in QueueType]: number } {
    return { priority: this.size('priority'), retry: this.size('retry'), paused: this.size('paused'), waiting: this.size('waiting'), completed: this.size('completed'), failed: this.size('failed'), cancelled: this.size('cancelled') }
  },

  clearQueue(queueType: QueueType): void {
    set(`${PREFIX}${queueType}`, [])
  },

  clearAll(): void {
    for (const type of ['priority', 'retry', 'paused', 'waiting', 'completed', 'failed', 'cancelled'] as QueueType[]) {
      this.clearQueue(type)
    }
  },
}
