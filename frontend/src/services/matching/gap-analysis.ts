import type { SkillGapAnalysis, SkillMatchDetail } from './types'
import type { Job } from '@/services/discovery/types'

export function generateSkillGapAnalysis(skillDetail: SkillMatchDetail, job: Job): SkillGapAnalysis {
  const missingSkills = skillDetail.missingSkills

  const recommendedLearning = missingSkills.map(skill => {
    let priority: 'high' | 'medium' | 'low' = 'medium'
    let reason = ''

    if (isRequiredSkill(skill, job)) {
      priority = 'high'
      reason = 'Required skill for this role'
    } else if (isHighPrioritySkill(skill)) {
      priority = 'high'
      reason = 'High-demand skill in the industry'
    } else if (isEmergingSkill(skill)) {
      priority = 'low'
      reason = 'Emerging technology - nice to have'
    } else {
      priority = 'medium'
      reason = 'Preferred skill that could strengthen your profile'
    }

    return { skill, priority, reason }
  })

  const quickWins = recommendedLearning
    .filter(r => r.priority === 'high')
    .map(r => r.skill)

  const longTermImprovements = recommendedLearning
    .filter(r => r.priority === 'low')
    .map(r => r.skill)

  return {
    missingSkills,
    recommendedLearning,
    quickWins,
    longTermImprovements,
    coveragePercent: skillDetail.coveragePercent,
  }
}

function isRequiredSkill(skill: string, job: Job): boolean {
  return job.requiredSkills.some(s => s.toLowerCase() === skill.toLowerCase())
}

const HIGH_PRIORITY_SKILLS = [
  'typescript', 'javascript', 'python', 'react', 'node.js', 'aws', 'docker',
  'kubernetes', 'sql', 'git', 'machine learning', 'ai',
]

function isHighPrioritySkill(skill: string): boolean {
  return HIGH_PRIORITY_SKILLS.includes(skill.toLowerCase())
}

const EMERGING_SKILLS = [
  'rust', 'webassembly', 'wasm', 'blockchain', 'web3', 'solidity', 'quantum computing',
  'edge computing', 'serverless', 'llm', 'langchain', 'vector database',
]

function isEmergingSkill(skill: string): boolean {
  return EMERGING_SKILLS.includes(skill.toLowerCase())
}
