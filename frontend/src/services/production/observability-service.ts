import type { CorrelationContext } from './production-types'
import { v4Service } from '../orchestration/utils'

let _correlationId: string | null = null

function generate(prefix = 'corr'): string {
  return v4Service.generate(prefix)
}

export const observabilityService = {
  getCorrelationId(): string {
    if (!_correlationId) _correlationId = generate()
    return _correlationId
  },

  setCorrelationId(id: string): void {
    _correlationId = id
  },

  resetCorrelationId(): void {
    _correlationId = generate()
  },

  createContext(overrides?: Partial<CorrelationContext>): CorrelationContext {
    return {
      correlationId: this.getCorrelationId(),
      requestId: v4Service.generate('req'),
      userId: overrides?.userId,
      sessionId: overrides?.sessionId,
      workflowId: overrides?.workflowId,
      browserId: overrides?.browserId,
      providerId: overrides?.providerId,
      ...overrides,
    }
  },

  startSpan(operation: string, context?: CorrelationContext): { spanId: string; startTime: number; operation: string; context: CorrelationContext } {
    return { spanId: v4Service.generate('span'), startTime: Date.now(), operation, context: context ?? this.createContext() }
  },

  endSpan(span: { spanId: string; startTime: number; operation: string; context: CorrelationContext }): number {
    return Date.now() - span.startTime
  },

  get context(): CorrelationContext {
    return this.createContext()
  },
}
