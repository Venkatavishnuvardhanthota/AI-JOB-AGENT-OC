import type { ExecutionMode, Workflow } from './types'

export const executionService = {
  async executeSequential(workflows: Workflow[], executor: (wf: Workflow) => Promise<boolean>): Promise<{ success: number; failed: number }> {
    let success = 0; let failed = 0
    for (const wf of workflows) {
      try {
        const ok = await executor(wf)
        if (ok) success++; else failed++
      } catch { failed++ }
    }
    return { success, failed }
  },

  async executeParallel(workflows: Workflow[], executor: (wf: Workflow) => Promise<boolean>, concurrency: number = 3): Promise<{ success: number; failed: number }> {
    let success = 0; let failed = 0
    const batches: Workflow[][] = []
    for (let i = 0; i < workflows.length; i += concurrency) {
      batches.push(workflows.slice(i, i + concurrency))
    }
    for (const batch of batches) {
      const results = await Promise.allSettled(batch.map(wf => executor(wf)))
      for (const r of results) {
        if (r.status === 'fulfilled' && r.value) success++; else failed++
      }
    }
    return { success, failed }
  },

  async execute(workflows: Workflow[], mode: ExecutionMode, executor: (wf: Workflow) => Promise<boolean>, concurrency?: number): Promise<{ success: number; failed: number }> {
    if (mode === 'parallel') return this.executeParallel(workflows, executor, concurrency ?? 3)
    return this.executeSequential(workflows, executor)
  },
}
