import { useJobStats, useProfileCompleteness, useApplications, useSavedJobs, useResumes } from '@/api/hooks'
import { StatCard } from '@/components/layout/stat-card'
import { PageHeader } from '@/components/layout/page-header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { WelcomeBanner } from '@/components/onboarding/welcome-banner'
import { OnboardingChecklist } from '@/components/onboarding/checklist'
import { ProfileCompletionCard } from '@/components/dashboard/profile-completion'
import { QuickActions } from '@/components/dashboard/quick-actions'
import { Briefcase, FileText, Eye, CheckCircle, Activity, Clock, Cpu } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { Link } from 'react-router-dom'
import { useState } from 'react'
import { timeAgo } from '@/lib/utils'

export function DashboardPage() {
  const { user } = useAuth()
  const { data: stats, isLoading: statsLoading } = useJobStats()
  const { data: completeness } = useProfileCompleteness() as any
  const { data: appsData, isLoading: appsLoading } = useApplications({ page_size: 5 })
  const { data: savedData, isLoading: savedLoading } = useSavedJobs({ page_size: 5 })
  const { data: resumes } = useResumes()

  const [dismissWelcome, setDismissWelcome] = useState(false)

  const loading = statsLoading || appsLoading || savedLoading

  const apps = (appsData as any)?.items || []
  const saved = (savedData as any)?.items || []
  const hasResumes = Array.isArray(resumes) && resumes.length > 0
  const completenessScore = completeness?.overall_score ?? 0
  const isFirstTime = !dismissWelcome && completenessScore === 0 && !hasResumes

  if (loading) {
    return (
      <div className="space-y-6" aria-label="Loading dashboard">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24 rounded-xl" />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Skeleton className="h-80 rounded-xl lg:col-span-2" />
          <Skeleton className="h-80 rounded-xl" />
        </div>
        <Skeleton className="h-48 rounded-xl" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Welcome back, ${[user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.email || 'User'}`}
        description="Here's an overview of your job search activity."
      />

      {isFirstTime && (
        <WelcomeBanner onDismiss={() => setDismissWelcome(true)} />
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Jobs" value={(stats as any)?.total ?? 0} icon={Briefcase} />
        <StatCard title="Saved Jobs" value={(savedData as any)?.total ?? 0} icon={Eye} />
        <StatCard title="Applications" value={(appsData as any)?.total ?? 0} icon={FileText} />
        <StatCard title="Applied" value={(stats as any)?.applied ?? 0} icon={CheckCircle} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {completenessScore < 100 && <OnboardingChecklist />}

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-primary" />
                Recent Applications
              </CardTitle>
            </CardHeader>
            <CardContent>
              {apps.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">No applications yet. Start applying to jobs!</p>
              ) : (
                <div className="space-y-2">
                  {apps.map((app: any) => (
                    <Link key={app.id} to={`/applications`} className="flex items-center justify-between p-3 rounded-lg hover:bg-white/5 transition-colors">
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{app.job_title || app.job_id}</p>
                        <p className="text-xs text-muted-foreground">{app.company_name || ''}</p>
                      </div>
                      <Badge variant={app.status === 'submitted' ? 'success' : app.status === 'prepared' ? 'warning' : 'secondary'}>
                        {app.status}
                      </Badge>
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <ProfileCompletionCard />
          <QuickActions />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-primary" />
              Recently Saved Jobs
            </CardTitle>
          </CardHeader>
          <CardContent>
            {saved.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">No saved jobs yet. Search and save jobs to track them.</p>
            ) : (
              <div className="space-y-2">
                {saved.slice(0, 5).map((job: any) => (
                  <Link key={job.id} to={`/jobs/${job.id}`} className="flex items-center justify-between p-3 rounded-lg hover:bg-white/5 transition-colors border border-glass-border">
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">{job.title}</p>
                      <p className="text-xs text-muted-foreground">{job.company_name} · {job.location || 'Remote'}</p>
                    </div>
                    <span className="text-xs text-muted-foreground shrink-0">{timeAgo(job.posted_at)}</span>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cpu className="h-5 w-5 text-primary" />
              System Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { label: 'Job Providers', status: 'active' as const },
                { label: 'Matching Engine', status: 'active' as const },
                { label: 'Application Pipeline', status: 'active' as const },
                { label: 'Profile Intelligence', status: (completeness ? 'active' : 'inactive') as 'active' | 'inactive' },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">{item.label}</span>
                  <Badge variant={item.status === 'active' ? 'success' : 'secondary'}>
                    {item.status === 'active' ? 'Online' : 'Setup Required'}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
