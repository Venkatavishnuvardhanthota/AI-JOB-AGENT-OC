import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScoreBadge } from '@/components/ScoreBadge'
import { getDecisionLabel } from '@/services/matching'
import type { MatchStatistics, Decision } from '@/services/matching'
import { Target, TrendingUp, Award, ThumbsUp, ThumbsDown } from 'lucide-react'

interface MatchDashboardProps {
  statistics: MatchStatistics
  totalJobs: number
}

const DECISION_ORDER: Decision[] = ['apply_immediately', 'high_priority', 'good_match', 'consider', 'low_match', 'skip']

export function MatchDashboard({ statistics, totalJobs }: MatchDashboardProps) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="text-center p-3 rounded-lg bg-dark-800">
          <div className="flex items-center justify-center mb-1"><Target className="w-4 h-4 text-blue-400" /></div>
          <div className="text-2xl font-bold text-blue-400">{totalJobs}</div>
          <p className="text-xs text-muted-foreground">Jobs Scored</p>
        </div>
        <div className="text-center p-3 rounded-lg bg-dark-800">
          <div className="flex items-center justify-center mb-1"><ScoreBadge score={statistics.averageScore} size="sm" /></div>
          <div className="text-2xl font-bold">{Math.round(statistics.averageScore * 100)}%</div>
          <p className="text-xs text-muted-foreground">Avg Match</p>
        </div>
        <div className="text-center p-3 rounded-lg bg-dark-800">
          <div className="flex items-center justify-center mb-1"><TrendingUp className="w-4 h-4 text-green-400" /></div>
          <div className="text-2xl font-bold text-green-400">{Math.round(statistics.averageConfidence * 100)}%</div>
          <p className="text-xs text-muted-foreground">Confidence</p>
        </div>
        <div className="text-center p-3 rounded-lg bg-dark-800">
          <div className="flex items-center justify-center mb-1"><Award className="w-4 h-4 text-purple-400" /></div>
          <div className="text-2xl font-bold text-purple-400">{Math.round(statistics.averageSkillScore * 100)}%</div>
          <p className="text-xs text-muted-foreground">Skills</p>
        </div>
        <div className="text-center p-3 rounded-lg bg-dark-800">
          <div className="flex items-center justify-center mb-1"><ThumbsUp className="w-4 h-4 text-emerald-400" /></div>
          <div className="text-2xl font-bold text-emerald-400">{statistics.decisionBreakdown.apply_immediately || 0}</div>
          <p className="text-xs text-muted-foreground">Apply Now</p>
        </div>
        <div className="text-center p-3 rounded-lg bg-dark-800">
          <div className="flex items-center justify-center mb-1"><ThumbsDown className="w-4 h-4 text-red-400" /></div>
          <div className="text-2xl font-bold text-red-400">{statistics.decisionBreakdown.skip || 0}</div>
          <p className="text-xs text-muted-foreground">Skipped</p>
        </div>
      </div>

      {statistics.decisionBreakdown && Object.keys(statistics.decisionBreakdown).length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-sm">Recommendation Breakdown</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {DECISION_ORDER.filter(d => (statistics.decisionBreakdown[d] || 0) > 0).map(decision => {
                const count = statistics.decisionBreakdown[decision] || 0
                const pct = totalJobs > 0 ? Math.round((count / totalJobs) * 100) : 0
                return (
                  <div key={decision} className="flex items-center gap-3">
                    <span className="text-xs w-28 shrink-0">{getDecisionLabel(decision)}</span>
                    <div className="flex-1 h-4 bg-dark-700 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-primary to-primary/60"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="text-xs w-16 text-right">{count} ({pct}%)</span>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {statistics.topSkills.length > 0 && (
          <Card>
            <CardHeader><CardTitle className="text-sm">Top Skills in Jobs</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                {statistics.topSkills.slice(0, 8).map(({ skill, count }) => (
                  <div key={skill} className="flex items-center justify-between text-xs">
                    <span>{skill}</span>
                    <span className="text-muted-foreground">{count} jobs</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
        {statistics.commonMissingSkills.length > 0 && (
          <Card>
            <CardHeader><CardTitle className="text-sm">Most Common Missing Skills</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                {statistics.commonMissingSkills.slice(0, 8).map(({ skill, count }) => (
                  <div key={skill} className="flex items-center justify-between text-xs">
                    <span className="text-yellow-400">{skill}</span>
                    <span className="text-muted-foreground">{count} jobs</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
