import { useProfileCompleteness } from '@/api/hooks'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { Link } from 'react-router-dom'
import { AlertCircle } from 'lucide-react'

const categoryLabels: Record<string, { label: string; weight: number }> = {
  career_profile: { label: 'Basic Info', weight: 20 },
  skills: { label: 'Skills', weight: 15 },
  education: { label: 'Education', weight: 15 },
  experience: { label: 'Experience', weight: 20 },
  projects: { label: 'Projects', weight: 10 },
  certifications: { label: 'Certifications', weight: 8 },
  languages: { label: 'Languages', weight: 5 },
  social_links: { label: 'Social Links', weight: 5 },
  preferences: { label: 'Preferences', weight: 2 },
}

export function ProfileCompletionCard() {
  const { data: completeness, isLoading } = useProfileCompleteness() as any

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Profile Completion</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-4 w-full mb-4" />
          <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-3 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  const score = completeness?.overall_score ?? 0
  const categories = (completeness?.categories as Record<string, number>) ?? {}
  const missingItems = (completeness?.missing_items as string[]) ?? []

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Profile Completion</span>
          <span className="text-2xl font-bold text-primary">{Math.round(score)}%</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Progress value={score} className="mb-4" aria-label={`Profile ${Math.round(score)}% complete`} />

        <div className="space-y-2 mb-4">
          {Object.entries(categoryLabels).map(([key, { label, weight }]) => {
            const catScore = categories[key] ?? 0
            return (
              <div key={key} className="flex items-center gap-2 text-xs">
                <span className="text-muted-foreground min-w-24">{label}</span>
                <div className="flex-1 h-1.5 rounded-full bg-dark-700 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-primary/60 transition-all"
                    style={{ width: `${catScore}%` }}
                  />
                </div>
                <span className="text-muted-foreground min-w-8 text-right">{weight}%</span>
              </div>
            )
          })}
        </div>

        {missingItems.length > 0 && (
          <div className="space-y-1.5">
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <AlertCircle className="h-3 w-3" />
              Missing:
            </p>
            <div className="flex flex-wrap gap-1.5">
              {missingItems.map((item) => (
                <span key={item} className="inline-flex items-center text-xs text-error bg-error/10 rounded-full px-2 py-0.5">
                  {categoryLabels[item]?.label || item}
                </span>
              ))}
            </div>
          </div>
        )}

        <Button variant="outline" size="sm" className="w-full mt-4" asChild>
          <Link to="/profile">Complete Profile</Link>
        </Button>
      </CardContent>
    </Card>
  )
}
