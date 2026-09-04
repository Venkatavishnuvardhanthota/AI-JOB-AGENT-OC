import { useProfileCompleteness } from '@/api/hooks'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { Link } from 'react-router-dom'
import { AlertCircle } from 'lucide-react'

const BASIC_INFO_FIELDS = [
  'headline', 'professional_summary', 'total_years_experience', 'current_role',
  'desired_role', 'employment_status', 'current_salary', 'expected_salary',
  'salary_preference', 'willing_to_relocate', 'notice_period', 'portfolio_url',
  'linkedin_url', 'github_url', 'website_url',
]

const sectionRows: { key: string; label: string; weight: number }[] = [
  { key: 'education', label: 'Education', weight: 8 },
  { key: 'experience', label: 'Experience', weight: 8 },
  { key: 'skills', label: 'Skills', weight: 8 },
  { key: 'projects', label: 'Projects', weight: 4 },
  { key: 'certifications', label: 'Certifications', weight: 4 },
  { key: 'languages', label: 'Languages', weight: 4 },
  { key: 'achievements', label: 'Achievements', weight: 5 },
  { key: 'social_links', label: 'Social Links', weight: 5 },
]

const BASIC_INFO_WEIGHT = 54

function missingLabel(key: string): string {
  if (BASIC_INFO_FIELDS.includes(key)) return 'Basic Info'
  return sectionRows.find(r => r.key === key)?.label || key
}

export function ProfileCompletionCard() {
  const { data: completeness, isLoading } = useProfileCompleteness()

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

  const score = completeness?.percentage ?? 0
  const breakdown = completeness?.breakdown ?? {}
  const missingSections = completeness?.missing_sections ?? []

  const basicInfoScore = BASIC_INFO_FIELDS.reduce((sum, key) => sum + (breakdown[key] ?? 0), 0)
  const basicInfoPct = Math.min(100, Math.round((basicInfoScore / BASIC_INFO_WEIGHT) * 100))

  const rows = [
    { label: 'Basic Info', weight: BASIC_INFO_WEIGHT, pct: basicInfoPct },
    ...sectionRows.map(r => ({
      label: r.label,
      weight: r.weight,
      pct: Math.min(100, Math.round(((breakdown[r.key] ?? 0) / r.weight) * 100)),
    })),
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Profile Completion</span>
          <span className="text-2xl font-bold text-primary">{score}%</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Progress value={score} className="mb-4" aria-label={`Profile ${score}% complete`} />

        <div className="space-y-2 mb-4">
          {rows.map(({ label, weight, pct }) => (
            <div key={label} className="flex items-center gap-2 text-xs">
              <span className="text-muted-foreground min-w-24">{label}</span>
              <div className="flex-1 h-1.5 rounded-full bg-dark-700 overflow-hidden">
                <div
                  className="h-full rounded-full bg-primary/60 transition-all"
                  style={{ width: `${pct}%` }}
                />
              </div>
              <span className="text-muted-foreground min-w-8 text-right">{weight}%</span>
            </div>
          ))}
        </div>

        {missingSections.length > 0 && (
          <div className="space-y-1.5">
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <AlertCircle className="h-3 w-3" />
              Missing:
            </p>
            <div className="flex flex-wrap gap-1.5">
              {missingSections.map((item) => (
                <span key={item} className="inline-flex items-center text-xs text-error bg-error/10 rounded-full px-2 py-0.5">
                  {missingLabel(item)}
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
