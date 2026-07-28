import type { Checkpoint } from './types'
import type { ProviderId } from '../discovery/types'

const STORAGE_PREFIX = 'ajapp_ape_ckpt_'

function getStorageKey(workflowId: string): string {
  return STORAGE_PREFIX + workflowId
}

export const checkpointService = {
  save(workflowId: string, checkpoint: Checkpoint): void {
    try {
      const existing = this.getAll(workflowId)
      const existingIndex = existing.findIndex(c => c.stepIndex === checkpoint.stepIndex)
      if (existingIndex >= 0) {
        existing[existingIndex] = checkpoint
      } else {
        existing.push(checkpoint)
      }
      localStorage.setItem(getStorageKey(workflowId), JSON.stringify(existing))
    } catch {
    }
  },

  getLatest(workflowId: string): Checkpoint | null {
    const all = this.getAll(workflowId)
    return all.length > 0 ? all[all.length - 1] : null
  },

  getByStep(workflowId: string, stepIndex: number): Checkpoint | null {
    const all = this.getAll(workflowId)
    return all.find(c => c.stepIndex === stepIndex) ?? null
  },

  getAll(workflowId: string): Checkpoint[] {
    try {
      const raw = localStorage.getItem(getStorageKey(workflowId))
      return raw ? JSON.parse(raw) : []
    } catch {
      return []
    }
  },

  deleteAll(workflowId: string): void {
    try {
      localStorage.removeItem(getStorageKey(workflowId))
    } catch {
    }
  },

  deleteByStep(workflowId: string, stepIndex: number): void {
    const all = this.getAll(workflowId).filter(c => c.stepIndex !== stepIndex)
    try {
      localStorage.setItem(getStorageKey(workflowId), JSON.stringify(all))
    } catch {
    }
  },

  create(
    workflowId: string,
    applicationUrl: string,
    providerId: ProviderId,
    stepIndex: number,
    completedFields: string[],
    fieldValues: Record<string, string>,
    uploadedDocuments: string[],
    lastAction: string
  ): Checkpoint {
    return {
      id: `ckpt_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      workflowId,
      applicationUrl,
      providerId,
      stepIndex,
      completedFields,
      fieldValues,
      uploadedDocuments,
      lastAction,
      timestamp: new Date().toISOString(),
    }
  },
}
