import { describe, it, expect } from 'vitest'
import {
  canTransition,
  getStatusLabel,
  getStatusCategory,
  APPLICATION_STATUSES,
} from './status'

describe('StatusService', () => {
  it('has all 15 statuses', () => {
    expect(APPLICATION_STATUSES).toHaveLength(15)
  })

  it('allows saved to preparing', () => {
    expect(canTransition('saved', 'preparing')).toBe(true)
  })

  it('disallows saved to applied', () => {
    expect(canTransition('saved', 'applied')).toBe(false)
  })

  it('returns label for saved', () => {
    expect(getStatusLabel('saved')).toBe('Saved')
  })

  it('returns label for ready_to_apply', () => {
    expect(getStatusLabel('ready_to_apply')).toBe('Ready To Apply')
  })

  it('categorizes saved as preparation', () => {
    expect(getStatusCategory('saved')).toBe('preparation')
  })

  it('categorizes applied as active', () => {
    expect(getStatusCategory('applied')).toBe('active')
  })

  it('categorizes technical_interview as interview', () => {
    expect(getStatusCategory('technical_interview')).toBe('interview')
  })

  it('categorizes offer as offer', () => {
    expect(getStatusCategory('offer')).toBe('offer')
  })

  it('categorizes accepted as final', () => {
    expect(getStatusCategory('accepted')).toBe('final')
  })
})
