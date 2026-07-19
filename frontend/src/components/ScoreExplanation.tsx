import type { ScoreExplanation as ScoreExplanationType } from '../types'
import { ScoreBadge } from './ScoreBadge'

interface ScoreExplanationProps {
  explanations: ScoreExplanationType[]
  overall?: number
}

const CATEGORY_COLORS: Record<string, string> = {
  skill: '#3b82f6',
  keyword: '#8b5cf6',
  experience: '#06b6d4',
  education: '#f59e0b',
  company: '#ec4899',
}

export function ScoreExplanationPanel({ explanations, overall }: ScoreExplanationProps) {
  return (
    <div style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 16, maxWidth: 480 }}>
      {overall != null && (
        <div style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
          <ScoreBadge score={overall} size="lg" />
          <span style={{ fontWeight: 600, fontSize: 16 }}>Overall Match</span>
        </div>
      )}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {explanations.map((exp) => (
          <div key={exp.category} style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
            <div
              style={{
                width: 4,
                height: '100%',
                minHeight: 40,
                backgroundColor: CATEGORY_COLORS[exp.category] || '#9ca3af',
                borderRadius: 2,
                flexShrink: 0,
              }}
            />
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                <ScoreBadge score={exp.score} size="sm" />
                <span style={{ fontSize: 13, fontWeight: 600, textTransform: 'capitalize' }}>
                  {exp.category}
                </span>
                <span style={{ fontSize: 11, color: '#9ca3af' }}>
                  (weight: {Math.round(exp.weight * 100)}%)
                </span>
              </div>
              <p style={{ fontSize: 12, color: '#6b7280', margin: 0, lineHeight: 1.4 }}>{exp.details}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
