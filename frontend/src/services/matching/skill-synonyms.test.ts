import { describe, it, expect } from 'vitest'
import { normalizeSkill, areSkillsSimilar, findMatchingSkills } from './skill-synonyms'

describe('normalizeSkill', () => {
  it('normalizes common variations', () => {
    expect(normalizeSkill('Node.js')).toBe('node.js')
    expect(normalizeSkill('nodejs')).toBe('node.js')
    expect(normalizeSkill('ReactJS')).toBe('react')
    expect(normalizeSkill('JS')).toBe('javascript')
    expect(normalizeSkill('Golang')).toBe('go')
    expect(normalizeSkill('K8s')).toBe('kubernetes')
  })

  it('returns lowercase for unknown skills', () => {
    expect(normalizeSkill('SomeRandomSkill')).toBe('somerandomskill')
  })
})

describe('areSkillsSimilar', () => {
  it('returns true for synonyms', () => {
    expect(areSkillsSimilar('Node.js', 'nodejs')).toBe(true)
    expect(areSkillsSimilar('React', 'ReactJS')).toBe(true)
    expect(areSkillsSimilar('JS', 'JavaScript')).toBe(true)
  })

  it('returns false for different skills', () => {
    expect(areSkillsSimilar('React', 'Angular')).toBe(false)
  })
})

describe('findMatchingSkills', () => {
  it('finds exact matches', () => {
    const result = findMatchingSkills(['React', 'Node.js'], ['React', 'Node.js'])
    expect(result.exact).toHaveLength(2)
    expect(result.missing).toHaveLength(0)
  })

  it('finds similar matches via synonyms', () => {
    const result = findMatchingSkills(['ReactJS', 'nodejs'], ['React', 'Node.js'])
    expect(result.exact).toHaveLength(2)
  })

  it('detects missing skills', () => {
    const result = findMatchingSkills(['React'], ['React', 'Python', 'AWS'])
    expect(result.exact).toHaveLength(1)
    expect(result.missing).toHaveLength(2)
    expect(result.missing).toContain('Python')
    expect(result.missing).toContain('AWS')
  })
})
