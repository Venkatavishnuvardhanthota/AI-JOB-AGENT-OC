import { useAtsAnalysis } from '@/api/hooks'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { AlertTriangle, CheckCircle2, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AtsScoreProps {
  resumeId: string
}

function ScoreBar({ value, label }: { value: number; label: string }) {
  const color = value >= 70 ? 'bg-success' : value >= 40 ? 'bg-warning' : 'bg-error'
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span>{label}</span>
        <span className={cn('font-mono font-medium', value >= 70 ? 'text-success' : value >= 40 ? 'text-warning' : 'text-error')}>
          {value}%
        </span>
      </div>
      <div className="h-2 rounded-full bg-dark-700 overflow-hidden">
        <div className={cn('h-full rounded-full transition-all', color)} style={{ width: `${value}%` }} />
      </div>
    </div>
  )
}

export function AtsScore({ resumeId }: AtsScoreProps) {
  const { data, isLoading } = useAtsAnalysis(resumeId) as any

  if (isLoading) return <Skeleton className="h-48 w-full rounded-xl" />

  if (!data) return <p className="text-sm text-muted-foreground">Unable to analyze ATS compatibility.</p>

  const { overall, categories, strengths, improvements } = data
  const overallColor = overall >= 70 ? 'text-success' : overall >= 40 ? 'text-warning' : 'text-error'

  return (
    <div className="space-y-6" role="region" aria-label="ATS Compatibility Analysis">
      <div className="flex items-center gap-4">
        <div className={cn('text-4xl font-bold font-mono', overallColor)}>{overall}%</div>
        <div>
          <p className="font-semibold">ATS Compatibility</p>
          <p className="text-sm text-muted-foreground">
            {overall >= 70 ? 'Your resume is well-optimized for ATS systems.' :
             overall >= 40 ? 'Your resume needs improvements for better ATS matching.' :
             'Your resume may not pass ATS screening.'}
          </p>
        </div>
      </div>

      <div className="grid gap-4">
        {categories.map((cat: any) => (
          <Card key={cat.name} className="border-glass-border">
            <CardContent className="p-4">
              <ScoreBar value={cat.score} label={cat.name} />
              <p className="text-xs text-muted-foreground mt-2">{cat.reason}</p>
              {cat.missing && cat.missing.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs font-medium text-warning mb-1">Missing elements:</p>
                  <div className="flex flex-wrap gap-1">
                    {cat.missing.map((m: string) => (
                      <Badge key={m} variant="outline" className="text-[10px]">{m}</Badge>
                    ))}
                  </div>
                </div>
              )}
              <p className="text-xs text-primary mt-2">
                <Info className="h-3 w-3 inline mr-1" />{cat.suggestion}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="border-success/20 bg-success/5">
          <CardContent className="p-4">
            <h4 className="text-sm font-semibold text-success flex items-center gap-1 mb-2">
              <CheckCircle2 className="h-4 w-4" /> Strengths
            </h4>
            <ul className="space-y-1">
              {strengths.map((s: string, i: number) => (
                <li key={i} className="text-xs text-muted-foreground flex items-start gap-1">
                  <span className="text-success mt-0.5">✓</span> {s}
                </li>
              ))}
              {strengths.length === 0 && <li className="text-xs text-muted-foreground">No strengths identified yet.</li>}
            </ul>
          </CardContent>
        </Card>

        <Card className="border-warning/20 bg-warning/5">
          <CardContent className="p-4">
            <h4 className="text-sm font-semibold text-warning flex items-center gap-1 mb-2">
              <AlertTriangle className="h-4 w-4" /> Needs Improvement
            </h4>
            <ul className="space-y-1">
              {improvements.map((s: string, i: number) => (
                <li key={i} className="text-xs text-muted-foreground flex items-start gap-1">
                  <span className="text-warning mt-0.5">•</span> {s}
                </li>
              ))}
              {improvements.length === 0 && <li className="text-xs text-muted-foreground">No improvements needed.</li>}
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
