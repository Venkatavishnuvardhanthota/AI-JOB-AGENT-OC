import { useMemo } from 'react'
import { useCoverLetter, useResume, useJobs } from '@/api/hooks'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import { CheckCircle2, Circle, FileText, Mail, Briefcase, Building2, Download, Package } from 'lucide-react'

interface AppPackageReviewProps {
  jobId: string
  resumeId: string
  coverLetterId: string
  onDownload?: (id: string, format: string) => void
}

export function ApplicationPackageReview({ jobId, resumeId, coverLetterId, onDownload }: AppPackageReviewProps) {
  const { data: coverLetter, isLoading: clLoading } = useCoverLetter(coverLetterId) as any
  const { data: resume, isLoading: resLoading } = useResume(resumeId) as any
  const { data: jobs, isLoading: jobsLoading } = useJobs() as any
  const job = useMemo(() => {
    const list = (jobs as any) || []
    return list.find((j: any) => j.id === jobId)
  }, [jobId, jobs])

  const loading = clLoading || resLoading || jobsLoading

  const checklist = useMemo(() => {
    const items = [
      { label: 'Resume Ready', met: !!resume, icon: FileText },
      { label: 'Cover Letter Ready', met: !!(coverLetter && coverLetter.status === 'ready'), icon: Mail },
      { label: 'Job Selected', met: !!job, icon: Briefcase },
      { label: 'Company Identified', met: !!(job?.company), icon: Building2 },
      { label: 'Content Complete', met: !!(coverLetter?.content && coverLetter.content.length > 100), icon: FileText },
    ]
    return { items, allMet: items.every(i => i.met), metCount: items.filter(i => i.met).length, total: items.length }
  }, [resume, coverLetter, job])

  return (
    <div className="space-y-6" role="region" aria-label="Application package review">
      <div className="flex items-center gap-2 pb-3 border-b border-glass-border">
        <Package className="h-5 w-5 text-accent" />
        <h3 className="font-semibold">Application Package Review</h3>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(i => <Skeleton key={i} className="h-20 rounded-xl" />)}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className={cn(resume ? 'border-success/30' : 'border-glass-border')}>
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <FileText className="h-4 w-4 text-primary" />
                  <h4 className="text-sm font-medium">Resume</h4>
                  {resume ? <Badge variant="success" className="text-[10px] ml-auto">Ready</Badge> : <Badge variant="warning" className="text-[10px] ml-auto">Missing</Badge>}
                </div>
                {resume ? (
                  <div>
                    <p className="text-xs font-medium">{resume.title || 'Untitled'}</p>
                    <p className="text-xs text-muted-foreground">v{resume.version} · {resume.template || 'No template'}</p>
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground">No resume selected</p>
                )}
              </CardContent>
            </Card>

            <Card className={cn(coverLetter?.status === 'ready' ? 'border-success/30' : 'border-glass-border')}>
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Mail className="h-4 w-4 text-accent" />
                  <h4 className="text-sm font-medium">Cover Letter</h4>
                  {coverLetter?.status === 'ready' ? <Badge variant="success" className="text-[10px] ml-auto">Ready</Badge> : <Badge variant="warning" className="text-[10px] ml-auto">{coverLetter?.status || 'Missing'}</Badge>}
                </div>
                {coverLetter ? (
                  <div>
                    <p className="text-xs font-medium">{coverLetter.title || 'Untitled'}</p>
                    <p className="text-xs text-muted-foreground">v{coverLetter.version} · {coverLetter.tone || 'professional'}</p>
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground">No cover letter</p>
                )}
              </CardContent>
            </Card>

            <Card className={cn(job ? 'border-success/30' : 'border-glass-border')}>
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Briefcase className="h-4 w-4 text-secondary" />
                  <h4 className="text-sm font-medium">Job</h4>
                  {job ? <Badge variant="success" className="text-[10px] ml-auto">Selected</Badge> : <Badge variant="warning" className="text-[10px] ml-auto">Missing</Badge>}
                </div>
                {job ? (
                  <div>
                    <p className="text-xs font-medium">{job.title || job.name}</p>
                    <p className="text-xs text-muted-foreground">{job.company}{job.location ? ` · ${job.location}` : ''}</p>
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground">No job selected</p>
                )}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardContent className="p-4">
              <h4 className="text-sm font-semibold mb-3">Application Checklist</h4>
              <div className="space-y-2">
                {checklist.items.map(item => (
                  <div key={item.label} className="flex items-center gap-2 text-sm">
                    {item.met ? (
                      <CheckCircle2 className="h-4 w-4 text-success" />
                    ) : (
                      <Circle className="h-4 w-4 text-muted-foreground" />
                    )}
                    <span className={item.met ? 'text-foreground' : 'text-muted-foreground'}>{item.label}</span>
                  </div>
                ))}
              </div>
              <div className="mt-3 pt-3 border-t border-glass-border flex items-center justify-between">
                <span className="text-xs text-muted-foreground">{checklist.metCount} of {checklist.total} complete</span>
                {checklist.allMet ? (
                  <Badge variant="success" className="text-xs">All Requirements Met</Badge>
                ) : (
                  <Badge variant="warning" className="text-xs">Incomplete</Badge>
                )}
              </div>
            </CardContent>
          </Card>

          {coverLetter?.id && (
            <div className="flex justify-end gap-2">
              {onDownload && (
                <>
                  <Button variant="outline" size="sm" onClick={() => onDownload(coverLetter.id, 'pdf')}>
                    <Download className="h-4 w-4 mr-1" /> Download PDF
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => onDownload(coverLetter.id, 'docx')}>
                    <Download className="h-4 w-4 mr-1" /> Download DOCX
                  </Button>
                </>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
