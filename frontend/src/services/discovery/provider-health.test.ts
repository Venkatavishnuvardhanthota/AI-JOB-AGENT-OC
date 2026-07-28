import { describe, it, expect, beforeEach } from 'vitest'
import { providerHealthService } from './provider-health'

describe('providerHealthService', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('returns default health for unknown provider', () => {
    const health = providerHealthService.get('linkedin' as any)
    expect(health.status).toBe('healthy')
    expect(health.successRate).toBe(1.0)
    expect(health.availability).toBe(1.0)
  })

  it('records a success', () => {
    providerHealthService.recordSuccess('linkedin' as any, 500)
    const health = providerHealthService.get('linkedin' as any)
    expect(health.lastSuccess).toBeDefined()
    expect(health.averageLatency).toBe(500)
    expect(health.status).toBe('healthy')
  })

  it('records a failure', () => {
    providerHealthService.recordFailure('indeed' as any, 'Timeout')
    const health = providerHealthService.get('indeed' as any)
    expect(health.lastFailure).toBeDefined()
    expect(health.lastError).toBe('Timeout')
    expect(health.errorCount).toBe(1)
    expect(health.consecutiveFailures).toBe(1)
  })

  it('degrades after consecutive failures', () => {
    for (let i = 0; i < 3; i++) {
      providerHealthService.recordFailure('test_provider' as any, `Error ${i}`)
    }
    const health = providerHealthService.get('test_provider' as any)
    expect(health.status).toBe('degraded')
    expect(health.consecutiveFailures).toBe(3)
  })

  it('marks unhealthy after 5 consecutive failures', () => {
    for (let i = 0; i < 5; i++) {
      providerHealthService.recordFailure('bad_provider' as any, `Err ${i}`)
    }
    const health = providerHealthService.get('bad_provider' as any)
    expect(health.status).toBe('unhealthy')
  })

  it('resets health', () => {
    providerHealthService.recordFailure('reset_provider' as any, 'Error')
    providerHealthService.reset('reset_provider' as any)
    const health = providerHealthService.get('reset_provider' as any)
    expect(health.errorCount).toBe(0)
    expect(health.successRate).toBe(1.0)
  })

  it('resets all health', () => {
    providerHealthService.recordFailure('linkedin' as any, 'E1')
    providerHealthService.recordFailure('indeed' as any, 'E2')
    providerHealthService.resetAll()
    expect(providerHealthService.get('linkedin' as any).errorCount).toBe(0)
    expect(providerHealthService.get('indeed' as any).errorCount).toBe(0)
  })
})
