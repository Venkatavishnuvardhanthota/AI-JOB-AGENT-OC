import { describe, it, expect, beforeEach } from 'vitest'
import { discoveryHistoryService } from './discovery-history'

describe('discoveryHistoryService', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('starts with empty history', () => {
    expect(discoveryHistoryService.getAll()).toHaveLength(0)
  })

  it('adds entries', () => {
    discoveryHistoryService.add({
      id: '1', query: 'engineer', location: null, timestamp: new Date().toISOString(),
      providersUsed: ['linkedin'], jobsFound: 10, duplicatesRemoved: 2, uniqueJobs: 8,
      errors: [], executionTime: 500, status: 'completed', profileId: null,
    })
    expect(discoveryHistoryService.getAll()).toHaveLength(1)
  })

  it('gets recent entries', () => {
    for (let i = 0; i < 5; i++) {
      discoveryHistoryService.add({
        id: `${i}`, query: `q${i}`, location: null, timestamp: new Date().toISOString(),
        providersUsed: [], jobsFound: i, duplicatesRemoved: 0, uniqueJobs: i,
        errors: [], executionTime: 100, status: 'completed', profileId: null,
      })
    }
    expect(discoveryHistoryService.getRecent(3)).toHaveLength(3)
  })

  it('computes statistics', () => {
    discoveryHistoryService.add({
      id: '1', query: 'engineer', location: null, timestamp: new Date().toISOString(),
      providersUsed: ['linkedin'], jobsFound: 10, duplicatesRemoved: 2, uniqueJobs: 8,
      errors: [], executionTime: 1000, status: 'completed', profileId: null,
    })
    const stats = discoveryHistoryService.getStatistics()
    expect(stats.totalSearches).toBe(1)
    expect(stats.totalJobsDiscovered).toBe(10)
    expect(stats.totalDuplicatesRemoved).toBe(2)
    expect(stats.averageExecutionTime).toBe(1000)
    expect(stats.searchesToday).toBe(1)
  })

  it('clears history', () => {
    discoveryHistoryService.add({
      id: '1', query: 'test', location: null, timestamp: new Date().toISOString(),
      providersUsed: [], jobsFound: 0, duplicatesRemoved: 0, uniqueJobs: 0,
      errors: [], executionTime: 0, status: 'completed', profileId: null,
    })
    discoveryHistoryService.clear()
    expect(discoveryHistoryService.getAll()).toHaveLength(0)
  })
})
