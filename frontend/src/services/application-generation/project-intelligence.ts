import type { ProjectRanking, GenerationRequest } from './types'

export function rankProjects(
  projects: { name: string; description: string; technologies: string[]; impact: number; recency: number; domain: string }[],
  request: GenerationRequest
): ProjectRanking[] {
  return projects.map(p => {
    const techOverlap = computeTechOverlap(p.technologies, request.requiredSkills)
    const domainMatch = computeDomainMatch(p.domain, request.companyIndustry || '')
    const overallScore = techOverlap * 0.4 + p.impact * 0.3 + p.recency * 0.2 + domainMatch * 0.1

    return {
      name: p.name,
      description: p.description,
      technologies: p.technologies,
      relevance: techOverlap,
      impact: p.impact,
      recency: p.recency,
      domainMatch,
      overallScore,
      included: overallScore > 0.3,
      exclusionReason: overallScore <= 0.3 ? 'Low relevance to job requirements' : null,
    }
  }).sort((a, b) => b.overallScore - a.overallScore)
}

function computeTechOverlap(projectTechs: string[], requiredSkills: string[]): number {
  if (projectTechs.length === 0 || requiredSkills.length === 0) return 0
  const required = new Set(requiredSkills.map(s => s.toLowerCase()))
  const matched = projectTechs.filter(t => required.has(t.toLowerCase()))
  return matched.length / Math.max(projectTechs.length, 1)
}

function computeDomainMatch(projectDomain: string, jobIndustry: string): number {
  if (!projectDomain || !jobIndustry) return 0.3
  return projectDomain.toLowerCase() === jobIndustry.toLowerCase() ? 1 : 0.3
}
