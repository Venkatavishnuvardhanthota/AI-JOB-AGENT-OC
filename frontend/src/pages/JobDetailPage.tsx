import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useJob, useJobMatch, useJobCompany } from '@/api/hooks'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Separator } from '@/components/ui/separator'
import { ApplyJobDialog } from '@/components/jobs/ApplyJobDialog'
import { ArrowLeft, Building, MapPin, DollarSign, Clock, ExternalLink, Briefcase, Star, Wand2 } from 'lucide-react'
import { formatSalary, timeAgo } from '@/lib/utils'

export function JobDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: job, isLoading: jobLoading } = useJob(id!) as any
  const { data: match } = useJobMatch(id!) as any
  const { data: company } = useJobCompany(id!) as any
  const [applyOpen, setApplyOpen] = useState(false)

  if (jobLoading) return <div className="space-y-4">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}</div>

  if (!job) return <div className="text-center py-16 text-muted-foreground">Job not found.</div>

  return (
    <div className="space-y-6 max-w-4xl">
      <Link to="/jobs/search" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Back to search
      </Link>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-foreground mb-1">{job.title}</h1>
              <p className="text-lg text-muted-foreground">{job.company_name}</p>
            </div>
            {match?.overall != null && (
              <div className="flex flex-col items-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-full border-2" style={{ borderColor: match.overall >= 60 ? 'var(--color-success)' : match.overall >= 40 ? 'var(--color-warning)' : 'var(--color-error)' }}>
                  <span className="text-xl font-bold">{Math.round(match.overall)}%</span>
                </div>
                <span className="text-xs text-muted-foreground mt-1">Match</span>
              </div>
            )}
          </div>

          <div className="flex flex-wrap gap-4 text-sm text-muted-foreground mb-4">
            {job.location && <span className="flex items-center gap-1"><MapPin className="h-4 w-4" />{job.remote ? 'Remote - ' : ''}{job.location}</span>}
            {(job.salary_min != null || job.salary_max != null) && <span className="flex items-center gap-1"><DollarSign className="h-4 w-4" />{formatSalary(job.salary_min, job.salary_max, job.salary_currency, job.salary_period)}</span>}
            {job.job_type && <span className="flex items-center gap-1"><Briefcase className="h-4 w-4" />{job.job_type}</span>}
            {job.posted_at && <span className="flex items-center gap-1"><Clock className="h-4 w-4" />{timeAgo(job.posted_at)}</span>}
            <Badge variant="secondary">{job.source}</Badge>
          </div>

          {job.skills && job.skills.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-4">
              {job.skills.map((skill: string) => <Badge key={skill} variant="outline">{skill}</Badge>)}
            </div>
          )}

          <Separator className="my-4" />

          <div className="prose prose-invert max-w-none text-sm text-muted-foreground whitespace-pre-wrap">
            {job.description || 'No description available.'}
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <Button onClick={() => setApplyOpen(true)}>
              <Wand2 className="h-4 w-4 mr-2" /> Apply with AI
            </Button>
            {job.apply_url && (
              <Button asChild variant="outline">
                <a href={job.apply_url} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="h-4 w-4 mr-2" /> Apply on {job.source}
                </a>
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <ApplyJobDialog
        jobId={id!}
        jobTitle={job.title}
        companyName={job.company_name}
        open={applyOpen}
        onClose={() => setApplyOpen(false)}
      />

      {match && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Star className="h-5 w-5 text-primary" />
              Match Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              {[
                { label: 'Skills', score: match.skill?.score },
                { label: 'Keywords', score: match.keyword?.score },
                { label: 'Experience', score: match.experience?.score },
                { label: 'Education', score: match.education?.score },
              ].map(item => (
                <div key={item.label} className="text-center p-3 rounded-lg bg-dark-800/50">
                  <div className="text-2xl font-bold mb-1">{item.score != null ? `${Math.round(item.score)}%` : '-'}</div>
                  <div className="text-xs text-muted-foreground">{item.label}</div>
                </div>
              ))}
            </div>
            {match.explanations && match.explanations.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Breakdown</h4>
                {match.explanations.map((exp: any, i: number) => (
                  <div key={i} className="flex items-center justify-between p-2 rounded bg-dark-800/30 text-sm">
                    <span className="text-muted-foreground">{exp.details || exp.category}</span>
                    <span className="font-medium">{Math.round(exp.score)}%</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {company && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building className="h-5 w-5 text-primary" />
              Company Research
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-invert max-w-none text-sm text-muted-foreground whitespace-pre-wrap">
              {typeof company === 'string' ? company : JSON.stringify(company, null, 2)}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
