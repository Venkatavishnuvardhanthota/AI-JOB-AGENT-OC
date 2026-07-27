import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { CheckCircle2, Circle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useProfile, useProfileSection, useResumes } from '@/api/hooks'

interface ChecklistItem {
  key: string
  label: string
  href: string
}

const checklistItems: ChecklistItem[] = [
  { key: 'profile', label: 'Complete Career Profile', href: '/profile' },
  { key: 'skills', label: 'Add Skills', href: '/profile' },
  { key: 'education', label: 'Add Education', href: '/profile' },
  { key: 'experience', label: 'Add Experience', href: '/profile' },
  { key: 'resume', label: 'Create or Import Resume', href: '/resumes' },
  { key: 'search', label: 'Search Jobs', href: '/jobs/search' },
  { key: 'match', label: 'Match Jobs', href: '/jobs/search' },
  { key: 'package', label: 'Generate Application Package', href: '/applications' },
  { key: 'apply', label: 'Run First Application', href: '/applications' },
]

export function OnboardingChecklist() {
  const { data: profile } = useProfile() as any
  const { data: skills } = useProfileSection<any>('skills')
  const { data: education } = useProfileSection<any>('education')
  const { data: experience } = useProfileSection<any>('experience')
  const { data: resumes } = useResumes()
  const hasResumes = Array.isArray(resumes) && resumes.length > 0
  const hasSkills = Array.isArray(skills) && skills.length > 0
  const hasEducation = Array.isArray(education) && education.length > 0
  const hasExperience = Array.isArray(experience) && experience.length > 0
  const hasProfile = profile?.headline || profile?.bio || profile?.location

  const completedMap: Record<string, boolean> = {
    profile: !!hasProfile,
    skills: hasSkills,
    education: hasEducation,
    experience: hasExperience,
    resume: hasResumes,
    search: false,
    match: false,
    package: false,
    apply: false,
  }

  const completedCount = Object.values(completedMap).filter(Boolean).length
  const totalCount = checklistItems.length
  const progress = Math.round((completedCount / totalCount) * 100)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Getting Started</span>
          <span className="text-sm text-muted-foreground font-normal">
            {completedCount}/{totalCount}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-4 h-1.5 w-full rounded-full bg-dark-700 overflow-hidden">
          <div
            className="h-full rounded-full bg-primary transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
        <ul className="space-y-1" role="list" aria-label="Onboarding checklist">
          {checklistItems.map((item) => {
            const done = completedMap[item.key]
            return (
              <li key={item.key}>
                <a
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-white/5",
                    done ? "text-muted-foreground" : "text-foreground"
                  )}
                  aria-label={`${item.label}${done ? ' (completed)' : ''}`}
                >
                  {done ? (
                    <CheckCircle2 className="h-4 w-4 text-success shrink-0" aria-hidden="true" />
                  ) : (
                    <Circle className="h-4 w-4 text-muted-foreground shrink-0" aria-hidden="true" />
                  )}
                  <span className={cn(done && "line-through")}>{item.label}</span>
                </a>
              </li>
            )
          })}
        </ul>
      </CardContent>
    </Card>
  )
}
