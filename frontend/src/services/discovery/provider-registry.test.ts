import { describe, it, expect, beforeEach } from 'vitest'
import { providerRegistry } from './provider-registry'

describe('providerRegistry', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('returns all default providers', () => {
    const providers = providerRegistry.getAll()
    expect(providers.length).toBeGreaterThanOrEqual(10)
    expect(providers.find(p => p.id === 'linkedin')).toBeDefined()
    expect(providers.find(p => p.id === 'indeed')).toBeDefined()
  })

  it('returns enabled providers only', () => {
    const enabled = providerRegistry.getEnabled()
    expect(enabled.length).toBeGreaterThan(0)
    expect(enabled.every(p => p.enabled)).toBe(true)
  })

  it('gets a provider by id', () => {
    const p = providerRegistry.get('linkedin')
    expect(p).toBeDefined()
    expect(p!.id).toBe('linkedin')
  })

  it('enables and disables providers', () => {
    providerRegistry.disable('naukri')
    expect(providerRegistry.get('naukri')!.enabled).toBe(false)
    expect(providerRegistry.getEnabled().find(p => p.id === 'naukri')).toBeUndefined()
    providerRegistry.enable('naukri')
    expect(providerRegistry.get('naukri')!.enabled).toBe(true)
  })

  it('returns prioritized providers', () => {
    const prioritized = providerRegistry.getPrioritized()
    for (let i = 1; i < prioritized.length; i++) {
      expect(prioritized[i - 1].priority).toBeLessThanOrEqual(prioritized[i].priority)
    }
  })

  it('returns capabilities', () => {
    const capabilities = providerRegistry.getCapabilities()
    expect(capabilities).toContain('search')
  })

  it('checks capability', () => {
    expect(providerRegistry.hasCapability('search')).toBe(true)
  })

  it('gets providers by capability', () => {
    const providers = providerRegistry.getByCapability('easy_apply')
    expect(providers.length).toBeGreaterThan(0)
  })
})
