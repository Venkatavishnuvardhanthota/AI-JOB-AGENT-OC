import type { PipelineStage } from './types'
import { nowISO } from './utils'

export function createPipelineStages(): PipelineStage[] {
  const stages = ['discovered', 'matched', 'generating', 'queued', 'waiting_browser', 'navigating', 'filling', 'uploading', 'review', 'submitting', 'tracking', 'completed']
  return stages.map(name => ({ name, status: 'pending', startedAt: null, completedAt: null, duration: null, error: null }))
}

export function updateStage(stages: PipelineStage[], name: string, updates: Partial<PipelineStage>): PipelineStage[] {
  return stages.map(s => s.name === name ? { ...s, ...updates } : s)
}

export function getCurrentStage(stages: PipelineStage[]): PipelineStage | null {
  return stages.find(s => s.status === 'running') ?? null
}

export function getStageProgress(stages: PipelineStage[]): { completed: number; total: number; percent: number } {
  const total = stages.filter(s => s.name !== 'completed').length
  const completed = stages.filter(s => s.status === 'completed').length
  return { completed, total, percent: total > 0 ? Math.round((completed / total) * 100) : 0 }
}

export function failStage(stages: PipelineStage[], name: string, error: string): PipelineStage[] {
  return updateStage(stages, name, { status: 'failed', completedAt: nowISO(), error })
}

export function completeStage(stages: PipelineStage[], name: string): PipelineStage[] {
  const now = nowISO()
  return updateStage(stages, name, { status: 'completed', completedAt: now })
}
