import { useProfile, useProfileSection, useResumes, useApplications } from '@/api/hooks'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { CheckCircle2, Circle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Link } from 'react-router-dom'

interface ChecklistItem {
  key: string
  label: string
  href: string
}

const checklistItems: ChecklistItem[] = [
  { key: 'profile', label: 'Complete Profile', href: '/profile' },
  { key: 'skills', label: 'Add Skills', href: '/profile' },
  { key: 'education', label: 'Add Education', href: '/profile' },
  { key: 'experience', label: 'Add Experience', href: '/profile' },
  { key: 'resume', label: 'Upload Resume', href: '/resumes' },
  { key: 'career_profile', label: 'Create Career Profile', href: '/profile' },
  { key: 'save_job', label: 'Save First Job', href: '/jobs/search' },
  { key: 'cover_letter', label: 'Generate Cover Letter', href: '/cover-letters' },
  { key: 'application', label: 'Create First Application', href: '/applications' },
]

function getLocalChecklist(): Record<string, boolean> {
  try {
    return JSON.parse(localStorage.getItem('checklist_completed') || '{}')
  } catch { return {} }
}

function setLocalChecklist(key: string) {
  const current = getLocalChecklist()
  current[key] = true
  localStorage.setItem('checklist_completed', JSON.stringify(current))
}

export function OnboardingChecklist() {
  const { data: profile } = useProfile() as any
  const { data: skills } = useProfileSection<any>('skills')
  const { data: education } = useProfileSection<any>('education')
  const { data: experience } = useProfileSection<any>('experience')
  const { data: resumes } = useResumes()
  const { data: appsData } = useApplications() as any

  const localCompleted = getLocalChecklist()
  const hasResumes = Array.isArray(resumes) && resumes.length > 0
  const hasSkills = Array.isArray(skills) && skills.length > 0
  const hasEducation = Array.isArray(education) && education.length > 0
  const hasExperience = Array.isArray(experience) && experience.length > 0
  const hasProfile = profile?.headline || profile?.professional_summary || profile?.current_role
  const appsCount = (appsData as any)?.items?.length || 0

  const completedMap: Record<string, boolean> = {
    profile: !!hasProfile,
    skills: hasSkills,
    education: hasEducation,
    experience: hasExperience,
    resume: hasResumes,
    career_profile: !!hasProfile,
    save_job: localCompleted.save_job || false,
    cover_letter: localCompleted.cover_letter || false,
    application: appsCount > 0 || localCompleted.application || false,
  }

  if (hasResumes) setLocalChecklist('resume')

  const completedCount = Object.values(completedMap).filter(Boolean).length
  const totalCount = checklistItems.length
  const progress = Math.round((completedCount / totalCount) * 100)

  return (
    <Card className="animate-in fade-in slide-in-from-bottom-2 duration-300">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Getting Started</span>
          <span className="text-sm text-muted-foreground font-normal">
            {completedCount}/{totalCount} ({progress}%)
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-4 h-1.5 w-full rounded-full bg-dark-700 overflow-hidden">
          <div
            className="h-full rounded-full bg-primary transition-all duration-700 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
        <ul className="space-y-1" role="list" aria-label="Onboarding checklist">
          {checklistItems.map((item) => {
            const done = completedMap[item.key]
            return (
              <li key={item.key}>
                <Link
                  to={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-white/5",
                    done ? "text-muted-foreground" : "text-foreground"
                  )}
                  aria-label={`${item.label}${done ? ' (completed)' : ''}`}
                >
                  {done ? (
                    <CheckCircle2 className="h-4 w-4 text-success shrink-0 transition-all duration-300" aria-hidden="true" />
                  ) : (
                    <Circle className="h-4 w-4 text-muted-foreground shrink-0" aria-hidden="true" />
                  )}
                  <span className={cn("transition-all duration-300", done && "line-through opacity-60")}>{item.label}</span>
                </Link>
              </li>
            )
          })}
        </ul>
      </CardContent>
    </Card>
  )
}
