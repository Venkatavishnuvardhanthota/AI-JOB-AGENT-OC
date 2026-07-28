import type { Checkpoint, WorkflowStage } from './types'
import { v4Service, nowISO } from './utils'

const PREFIX = 'ajapp_ork_cp_'

function get<T>(key: string, fallback: T): T { try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback } catch { return fallback } }
function set<T>(key: string, value: T): void { try { localStorage.setItem(key, JSON.stringify(value)) } catch {} }

export const checkpointService = {
  save(workflowId: string, stage: WorkflowStage, data: Record<string, unknown> = {}): Checkpoint {
    const cp: Checkpoint = { id: v4Service.generate('cp'), stage, timestamp: nowISO(), data, restored: false }
    const checkpoints = this.getCheckpoints(workflowId)
    checkpoints.push(cp)
    set(`${PREFIX}${workflowId}`, checkpoints.slice(-50))
    return cp
  },

  getCheckpoints(workflowId: string): Checkpoint[] {
    return get<Checkpoint[]>(`${PREFIX}${workflowId}`, [])
  },

  getLatest(workflowId: string): Checkpoint | null {
    const cps = this.getCheckpoints(workflowId)
    return cps.length > 0 ? cps[cps.length - 1] : null
  },

  getLatestByStage(workflowId: string, stage: WorkflowStage): Checkpoint | null {
    const cps = this.getCheckpoints(workflowId).filter(c => c.stage === stage)
    return cps.length > 0 ? cps[cps.length - 1] : null
  },

  restore(workflowId: string, checkpointId: string): Checkpoint | null {
    const cps = this.getCheckpoints(workflowId)
    const cp = cps.find(c => c.id === checkpointId)
    if (cp) {
      cp.restored = true
      set(`${PREFIX}${workflowId}`, cps)
    }
    return cp ?? null
  },

  restoreLatest(workflowId: string): Checkpoint | null {
    const latest = this.getLatest(workflowId)
    return latest ? this.restore(workflowId, latest.id) : null
  },

  clear(workflowId: string): void {
    set(`${PREFIX}${workflowId}`, [])
  },

  getRecoveryStages(): WorkflowStage[] {
    return ['waiting_browser', 'navigating', 'filling', 'uploading', 'submitting']
  },
}
