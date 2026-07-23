import { useJobStats, useProfileCompleteness, useApplications, useSavedJobs } from '@/api/hooks'
import { StatCard } from '@/components/layout/stat-card'
import { PageHeader } from '@/components/layout/page-header'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Briefcase, FileText, Eye, CheckCircle, UserCircle, Activity, Clock } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { Link } from 'react-router-dom'

export function DashboardPage() {
  const { user } = useAuth()
  const { data: stats, isLoading: statsLoading } = useJobStats()
  const { data: completeness } = useProfileCompleteness()
  const { data: appsData, isLoading: appsLoading } = useApplications({ page_size: 5 })
  const { data: savedData, isLoading: savedLoading } = useSavedJobs({ page_size: 5 })

  const loading = statsLoading || appsLoading || savedLoading

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24 rounded-xl" />)}
        </div>
        <Skeleton className="h-64 rounded-xl" />
      </div>
    )
  }

  const apps = (appsData as any)?.items || []
  const saved = (savedData as any)?.items || []
  const completenessScore = (completeness as any)?.score ?? 0

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Welcome back, ${user?.full_name || user?.email || 'User'}`}
        description="Here's an overview of your job search activity."
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Jobs" value={(stats as any)?.total ?? 0} icon={Briefcase} />
        <StatCard title="Saved Jobs" value={(savedData as any)?.total ?? 0} icon={Eye} />
        <StatCard title="Applications" value={(appsData as any)?.total ?? 0} icon={FileText} />
        <StatCard title="Applied" value={(stats as any)?.applied ?? 0} icon={CheckCircle} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
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
              <div className="space-y-3">
                {apps.map((app: any) => (
                  <Link key={app.id} to={`/applications`} className="flex items-center justify-between p-3 rounded-lg hover:bg-white/5 transition-colors">
                    <div>
                      <p className="text-sm font-medium">{app.job_title || app.job_id}</p>
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

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserCircle className="h-5 w-5 text-primary" />
              Profile Completeness
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center">
              <div className="relative h-24 w-24 mb-4">
                <svg className="h-24 w-24 -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="8" />
                  <circle cx="50" cy="50" r="42" fill="none" stroke="currentColor" strokeWidth="8" strokeDasharray={`${completenessScore * 2.64} 264`} className="text-primary transition-all duration-500" />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-2xl font-bold">{Math.round(completenessScore)}%</span>
              </div>
              {(completeness as any)?.missing && (completeness as any).missing.length > 0 && (
                <div className="w-full space-y-1">
                  <p className="text-xs text-muted-foreground mb-2">Missing items:</p>
                  {(completeness as any).missing.slice(0, 4).map((item: string) => (
                    <div key={item} className="text-xs text-muted-foreground flex items-center gap-1">
                      <span className="text-error">●</span> {item}
                    </div>
                  ))}
                </div>
              )}
              <Link to="/profile" className="mt-4 text-xs text-primary hover:underline">Complete Profile →</Link>
            </div>
          </CardContent>
        </Card>
      </div>

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
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {saved.map((job: any) => (
                <Link key={job.id} to={`/jobs/${job.id}`} className="p-3 rounded-lg hover:bg-white/5 transition-colors border border-glass-border">
                  <p className="text-sm font-medium">{job.title}</p>
                  <p className="text-xs text-muted-foreground">{job.company_name} · {job.location || 'Remote'}</p>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
