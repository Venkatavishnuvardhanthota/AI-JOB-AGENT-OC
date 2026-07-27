import { describe, it, expect } from 'vitest'
import { makeDecision, getDecisionLabel, getDecisionColor } from './decision-engine'

describe('makeDecision', () => {
  it('returns apply_immediately for high scores', () => {
    expect(makeDecision(0.9, 0.8, 0.8, true)).toBe('apply_immediately')
  })

  it('returns high_priority for good scores', () => {
    expect(makeDecision(0.8, 0.6, 0.6, false)).toBe('high_priority')
  })

  it('returns good_match for decent scores', () => {
    expect(makeDecision(0.65, 0.5, 0.4, false)).toBe('good_match')
  })

  it('returns consider for moderate scores', () => {
    expect(makeDecision(0.5, 0.4, 0.3, false)).toBe('consider')
  })

  it('returns low_match for low scores', () => {
    expect(makeDecision(0.3, 0.2, 0.2, false)).toBe('low_match')
  })

  it('returns skip for very low scores', () => {
    expect(makeDecision(0.1, 0.1, 0.1, false)).toBe('skip')
  })
})

describe('getDecisionLabel', () => {
  it('returns readable labels', () => {
    expect(getDecisionLabel('apply_immediately')).toBe('Apply Immediately')
    expect(getDecisionLabel('skip')).toBe('Skip')
  })
})

describe('getDecisionColor', () => {
  it('returns color classes', () => {
    expect(getDecisionColor('apply_immediately')).toContain('bg-green')
    expect(getDecisionColor('skip')).toContain('bg-gray')
  })
})
