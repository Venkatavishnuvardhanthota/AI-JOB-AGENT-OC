import type { Decision } from './types'

export function makeDecision(overall: number, confidence: number, skillScore: number, hasResume: boolean): Decision {
  if (overall >= 0.85 && confidence >= 0.7 && skillScore >= 0.7 && hasResume) {
    return 'apply_immediately'
  }

  if (overall >= 0.75 && skillScore >= 0.6) {
    return 'high_priority'
  }

  if (overall >= 0.6 && skillScore >= 0.4) {
    return 'good_match'
  }

  if (overall >= 0.4) {
    return 'consider'
  }

  if (overall >= 0.2) {
    return 'low_match'
  }

  return 'skip'
}

export function getDecisionLabel(decision: Decision): string {
  const labels: Record<Decision, string> = {
    apply_immediately: 'Apply Immediately',
    high_priority: 'High Priority',
    good_match: 'Good Match',
    consider: 'Consider',
    low_match: 'Low Match',
    skip: 'Skip',
  }
  return labels[decision]
}

export function getDecisionColor(decision: Decision): string {
  const colors: Record<Decision, string> = {
    apply_immediately: 'bg-green-500 text-white',
    high_priority: 'bg-emerald-500 text-white',
    good_match: 'bg-blue-500 text-white',
    consider: 'bg-yellow-500 text-black',
    low_match: 'bg-orange-500 text-white',
    skip: 'bg-gray-500 text-white',
  }
  return colors[decision]
}

export function getDecisionScore(decision: Decision): number {
  const scores: Record<Decision, number> = {
    apply_immediately: 100,
    high_priority: 85,
    good_match: 70,
    consider: 50,
    low_match: 30,
    skip: 10,
  }
  return scores[decision]
}
