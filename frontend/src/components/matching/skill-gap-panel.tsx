import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { SkillGapAnalysis } from '@/services/matching'
import { AlertTriangle, Lightbulb, Zap, BookOpen } from 'lucide-react'

interface SkillGapPanelProps {
  analysis: SkillGapAnalysis
}

export function SkillGapPanel({ analysis }: SkillGapPanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-yellow-400" />
          Skill Gap Analysis
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs text-muted-foreground">Coverage:</span>
            <div className="flex-1 h-2 bg-dark-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${analysis.coveragePercent >= 70 ? 'bg-green-500' : analysis.coveragePercent >= 40 ? 'bg-yellow-500' : 'bg-red-500'}`}
                style={{ width: `${analysis.coveragePercent}%` }}
              />
            </div>
            <span className="text-xs font-medium">{analysis.coveragePercent}%</span>
          </div>

          {analysis.missingSkills.length > 0 && (
            <div>
              <h4 className="text-xs font-medium mb-2 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3 text-red-400" />
                Missing Skills ({analysis.missingSkills.length})
              </h4>
              <div className="flex flex-wrap gap-1">
                {analysis.missingSkills.map(s => (
                  <Badge key={s} variant="destructive" className="text-[10px]">{s}</Badge>
                ))}
              </div>
            </div>
          )}

          {analysis.quickWins.length > 0 && (
            <div>
              <h4 className="text-xs font-medium mb-2 flex items-center gap-1">
                <Zap className="w-3 h-3 text-yellow-400" />
                Quick Wins
              </h4>
              <div className="flex flex-wrap gap-1">
                {analysis.quickWins.map(s => (
                  <Badge key={s} variant="secondary" className="text-[10px] bg-yellow-500/20 text-yellow-400">{s}</Badge>
                ))}
              </div>
            </div>
          )}

          {analysis.recommendedLearning.length > 0 && (
            <div>
              <h4 className="text-xs font-medium mb-2 flex items-center gap-1">
                <Lightbulb className="w-3 h-3 text-blue-400" />
                Recommended Learning
              </h4>
              <div className="space-y-1">
                {analysis.recommendedLearning.slice(0, 5).map(r => (
                  <div key={r.skill} className="flex items-center justify-between text-xs">
                    <span>{r.skill}</span>
                    <Badge variant="outline" className={`text-[10px] ${r.priority === 'high' ? 'border-red-500 text-red-400' : r.priority === 'medium' ? 'border-yellow-500 text-yellow-400' : 'border-blue-500 text-blue-400'}`}>
                      {r.priority}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}

          {analysis.longTermImprovements.length > 0 && (
            <div>
              <h4 className="text-xs font-medium mb-2 flex items-center gap-1">
                <BookOpen className="w-3 h-3 text-purple-400" />
                Long-term Improvements
              </h4>
              <div className="flex flex-wrap gap-1">
                {analysis.longTermImprovements.map(s => (
                  <Badge key={s} variant="outline" className="text-[10px]">{s}</Badge>
                ))}
              </div>
            </div>
          )}

          {analysis.missingSkills.length === 0 && (
            <p className="text-xs text-green-400">All skills matched! Great fit for this role.</p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
