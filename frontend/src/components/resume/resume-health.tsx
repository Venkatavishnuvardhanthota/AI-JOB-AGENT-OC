import { useResumeHealth } from '@/api/hooks'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

interface ResumeHealthProps {
  resumeId: string
}

export function ResumeHealth({ resumeId }: ResumeHealthProps) {
  const { data, isLoading } = useResumeHealth(resumeId) as any

  if (isLoading) return <Skeleton className="h-48 w-full rounded-xl" />

  if (!data) return <p className="text-sm text-muted-foreground">Unable to analyze resume health.</p>

  const { overall, strengths, improvements, recommendations } = data
  const colorClass = overall >= 70 ? 'text-success' : overall >= 40 ? 'text-warning' : 'text-error'
  const ringColor = overall >= 70 ? 'stroke-success' : overall >= 40 ? 'stroke-warning' : 'stroke-error'

  return (
    <div className="space-y-6" role="region" aria-label="Resume Health Report">
      <div className="flex items-center gap-6">
        <div className="relative h-24 w-24 flex items-center justify-center">
          <svg className="h-24 w-24 -rotate-90" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="42" fill="none" stroke="currentColor" className="text-dark-700" strokeWidth="8" />
            <circle cx="50" cy="50" r="42" fill="none" className={ringColor} strokeWidth="8"
              strokeDasharray={`${overall * 2.64} 264`} strokeLinecap="round" />
          </svg>
          <span className={cn('absolute text-2xl font-bold font-mono', colorClass)}>{overall}%</span>
        </div>
        <div>
          <p className="font-semibold text-lg">Resume Health</p>
          <p className="text-sm text-muted-foreground">
            {overall >= 70 ? 'Your resume is in good shape.' :
             overall >= 40 ? 'Your resume needs some work.' :
             'Your resume needs significant improvement.'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="border-success/20 bg-success/5">
          <CardContent className="p-4">
            <h4 className="text-sm font-semibold text-success mb-3">Strengths</h4>
            <div className="space-y-2">
              {strengths.map((s: any, i: number) => (
                <div key={i} className="flex items-start gap-2">
                  <span className="text-success mt-0.5 shrink-0">✓</span>
                  <div>
                    <p className="text-sm font-medium">{s.label}</p>
                    <p className="text-xs text-muted-foreground">{s.detail}</p>
                  </div>
                </div>
              ))}
              {strengths.length === 0 && <p className="text-xs text-muted-foreground">No strengths identified yet.</p>}
            </div>
          </CardContent>
        </Card>

        <Card className="border-warning/20 bg-warning/5">
          <CardContent className="p-4">
            <h4 className="text-sm font-semibold text-warning mb-3">Needs Improvement</h4>
            <div className="space-y-2">
              {improvements.map((s: any, i: number) => (
                <div key={i} className="flex items-start gap-2">
                  <span className="text-warning mt-0.5 shrink-0">⚠</span>
                  <div>
                    <p className="text-sm font-medium">{s.label}</p>
                    <p className="text-xs text-muted-foreground">{s.detail}</p>
                  </div>
                </div>
              ))}
              {improvements.length === 0 && <p className="text-xs text-muted-foreground">No improvements needed.</p>}
            </div>
          </CardContent>
        </Card>
      </div>

      {recommendations.length > 0 && (
        <Card>
          <CardContent className="p-4">
            <h4 className="text-sm font-semibold mb-3">Recommendations</h4>
            <ul className="space-y-1">
              {recommendations.map((r: string, i: number) => (
                <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                  <span className="text-primary mt-0.5">{i + 1}.</span>
                  {r}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
