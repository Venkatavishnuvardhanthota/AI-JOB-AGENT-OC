import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScoreBadge } from '@/components/ScoreBadge'
import type { MatchResult } from '@/services/matching'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { useState } from 'react'

interface MatchExplanationProps {
  match: MatchResult
}

export function MatchExplanation({ match }: MatchExplanationProps) {
  const [expanded, setExpanded] = useState(true)

  return (
    <Card>
      <CardHeader className="cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            Score Breakdown
          </CardTitle>
          <ScoreBadge score={match.overall} size="sm" />
        </div>
      </CardHeader>
      {expanded && (
        <CardContent>
          <div className="space-y-3">
            {match.explanations.map(exp => (
              <div key={exp.category} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${exp.type === 'positive' ? 'bg-green-400' : exp.type === 'negative' ? 'bg-red-400' : 'bg-yellow-400'}`} />
                    <span className="font-medium">{exp.category}</span>
                    <span className="text-muted-foreground">({exp.weight}%)</span>
                  </div>
                  <span className="font-medium">{Math.round(exp.score * 100)}%</span>
                </div>
                <div className="h-1.5 bg-dark-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${exp.type === 'positive' ? 'bg-green-500' : exp.type === 'negative' ? 'bg-red-500' : 'bg-yellow-500'}`}
                    style={{ width: `${exp.score * 100}%` }}
                  />
                </div>
                <p className="text-[10px] text-muted-foreground">{exp.details}</p>
              </div>
            ))}
          </div>
        </CardContent>
      )}
    </Card>
  )
}
