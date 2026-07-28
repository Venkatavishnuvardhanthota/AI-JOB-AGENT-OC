import type { ApprovalPoint, ExecutionMode } from './types'

export const approvalWorkflow = {
  shouldRequestApproval(
    mode: ExecutionMode,
    pointType: ApprovalPoint['type'],
    configuredPoints: ApprovalPoint['type'][]
  ): boolean {
    if (mode === 'automatic') return false
    return configuredPoints.includes(pointType)
  },

  createApprovalPoint(
    type: ApprovalPoint['type'],
    description: string
  ): ApprovalPoint {
    return {
      id: `ap_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      type,
      description,
      status: 'pending',
    }
  },

  approve(point: ApprovalPoint): ApprovalPoint {
    return { ...point, status: 'approved' }
  },

  reject(point: ApprovalPoint): ApprovalPoint {
    return { ...point, status: 'rejected' }
  },

  isApproved(point: ApprovalPoint | null): boolean {
    return point !== null && point.status === 'approved'
  },

  isRejected(point: ApprovalPoint | null): boolean {
    return point !== null && point.status === 'rejected'
  },

  isPending(point: ApprovalPoint | null): boolean {
    return point !== null && point.status === 'pending'
  },

  getDefaultApprovalPoints(mode: ExecutionMode): ApprovalPoint['type'][] {
    if (mode === 'automatic') return []
    return ['before_submission']
  },
}
