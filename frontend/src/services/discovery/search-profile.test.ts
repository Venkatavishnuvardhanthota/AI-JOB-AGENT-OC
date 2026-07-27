import { describe, it, expect, beforeEach } from 'vitest'
import { searchProfileService } from './search-profile'

describe('searchProfileService', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('creates a profile', () => {
    const profile = searchProfileService.create({
      name: 'Backend Developer',
      keywords: 'backend developer go',
      location: 'Remote',
      salaryMin: null,
      salaryMax: null,
      experienceLevel: null,
      employmentType: null,
      remote: null,
      enabledProviders: ['linkedin', 'indeed'],
      scheduleFrequency: 'daily',
    })
    expect(profile.id).toBeDefined()
    expect(profile.name).toBe('Backend Developer')
    expect(profile.scheduleFrequency).toBe('daily')
    expect(profile.createdAt).toBeDefined()
    expect(profile.lastRunAt).toBeNull()
  })

  it('gets all profiles', () => {
    searchProfileService.create({ name: 'P1', keywords: 'k1', location: null, salaryMin: null, salaryMax: null, experienceLevel: null, employmentType: null, remote: null, enabledProviders: ['linkedin'], scheduleFrequency: 'manual' })
    searchProfileService.create({ name: 'P2', keywords: 'k2', location: null, salaryMin: null, salaryMax: null, experienceLevel: null, employmentType: null, remote: null, enabledProviders: ['indeed'], scheduleFrequency: 'weekly' })
    expect(searchProfileService.getAll()).toHaveLength(2)
  })

  it('updates a profile', () => {
    const p = searchProfileService.create({ name: 'Test', keywords: 'test', location: null, salaryMin: null, salaryMax: null, experienceLevel: null, employmentType: null, remote: null, enabledProviders: [], scheduleFrequency: 'manual' })
    const updated = searchProfileService.update(p.id, { name: 'Updated' })
    expect(updated!.name).toBe('Updated')
    expect(searchProfileService.get(p.id)!.name).toBe('Updated')
  })

  it('removes a profile', () => {
    const p = searchProfileService.create({ name: 'Del', keywords: 'del', location: null, salaryMin: null, salaryMax: null, experienceLevel: null, employmentType: null, remote: null, enabledProviders: [], scheduleFrequency: 'manual' })
    searchProfileService.remove(p.id)
    expect(searchProfileService.get(p.id)).toBeUndefined()
  })

  it('marks profile as run', () => {
    const p = searchProfileService.create({ name: 'Run', keywords: 'run', location: null, salaryMin: null, salaryMax: null, experienceLevel: null, employmentType: null, remote: null, enabledProviders: [], scheduleFrequency: 'manual' })
    searchProfileService.markRun(p.id)
    expect(searchProfileService.get(p.id)!.lastRunAt).toBeDefined()
  })

  it('gets profiles by frequency', () => {
    searchProfileService.create({ name: 'D', keywords: 'd', location: null, salaryMin: null, salaryMax: null, experienceLevel: null, employmentType: null, remote: null, enabledProviders: [], scheduleFrequency: 'daily' })
    searchProfileService.create({ name: 'W', keywords: 'w', location: null, salaryMin: null, salaryMax: null, experienceLevel: null, employmentType: null, remote: null, enabledProviders: [], scheduleFrequency: 'weekly' })
    expect(searchProfileService.getByFrequency('daily')).toHaveLength(1)
    expect(searchProfileService.getByFrequency('weekly')).toHaveLength(1)
  })
})
