import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { applicationService } from '@/services/application'
import { PageHeader } from '@/components/layout/page-header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Select } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { useToast } from '@/components/ui/toast'
import { LoadingPage } from '@/components/layout/loading-page'
import {
  ApplicationStatusBadge,
  ApplicationPriorityBadge,
  ApplicationTimeline,
  ApplicationNotes,
  ApplicationActivity,
  ApplicationDocuments,
  InlineEdit,
} from '@/components/application'
import type { DocumentRef } from '@/components/application'
import { getAllowedTransitions, canTransition, getStatusLabel, PRIORITY_LABELS, PRIORITY_ORDER } from '@/services/status'
import { getReminderBadges } from '@/hooks/useReminderBadges'
import { getApplicationAge } from '@/hooks/useApplicationAge'
import {
  ArrowLeft, Building2, Briefcase,
  Globe, Trash2, AlertCircle, Clock, Wand2, Recycle, Sparkles,
} from 'lucide-react'
import type { ApplicationStatus, ApplicationPriority } from '@/types'

export function ApplicationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { addToast } = useToast()
  const [activeTab, setActiveTab] = useState('overview')
  const [statusError, setStatusError] = useState('')

  const { data: application, isLoading } = useQuery({
    queryKey: ['applications', id],
    queryFn: () => applicationService.get(id!),
    enabled: !!id,
  })

  const updateMutation = useMutation({
    mutationFn: (data: { status?: ApplicationStatus; priority?: ApplicationPriority }) =>
      applicationService.update(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications', id] })
      queryClient.invalidateQueries({ queryKey: ['applications'] })
      setStatusError('')
      addToast('Application updated', 'success')
    },
    onError: () => addToast('Failed to update application', 'error'),
  })

  const deleteMutation = useMutation({
    mutationFn: () => applicationService.delete(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] })
      addToast('Application deleted', 'info')
      navigate('/applications')
    },
    onError: () => addToast('Failed to delete application', 'error'),
  })

  const handleStatusChange = (newStatus: string) => {
    const s = newStatus as ApplicationStatus
    if (application && !canTransition(application.status, s)) {
      setStatusError(`Cannot transition from "${getStatusLabel(application.status)}" to "${getStatusLabel(s)}".`)
      return
    }
    setStatusError('')
    updateMutation.mutate({ status: s })
  }

  const handleFieldUpdate = (field: string, value: string) => {
    updateMutation.mutate({ [field]: value } as any)
  }

  if (isLoading) return <LoadingPage />

  if (!application) {
    return (
      <div className="space-y-6">
        <PageHeader title="Application not found" description="The application you're looking for doesn't exist." />
        <Link to="/applications"><Button variant="outline"><ArrowLeft className="h-4 w-4 mr-1" /> Back to Applications</Button></Link>
      </div>
    )
  }

  const allowedStatuses = getAllowedTransitions(application.status)
  const badges = getReminderBadges(application)
  const age = getApplicationAge(application.created_at)

  const documentRefs: { resume?: DocumentRef | null; coverLetter?: DocumentRef | null } = {
    resume: application.resume_id ? {
      id: application.resume_id,
      type: 'resume',
      name: `Resume for ${application.job_title}`,
      created_at: application.created_at,
    } : null,
    coverLetter: application.cover_letter_id ? {
      id: application.cover_letter_id,
      type: 'cover_letter',
      name: `Cover Letter for ${application.job_title}`,
      created_at: application.created_at,
    } : null,
  }

  const strategyLabels: Record<string, string> = {
    use_existing: 'Use Best Resume',
    tailor: 'Tailored Best Resume',
    generate: 'Generated New Resume',
    ask: 'Asked at apply time',
  }
  const hasStrategyInfo = !!(application.resume_strategy || application.generated || application.tailored)

  return (
    <div className="space-y-6">
      <PageHeader
        title={application.job_title}
        description={`${application.company_name}${application.location ? ` - ${application.location}` : ''}`}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => navigate('/applications')}>
              <ArrowLeft className="h-4 w-4 mr-1" /> Back
            </Button>
            <Button variant="destructive" size="sm" onClick={() => { if (confirm('Delete this application?')) deleteMutation.mutate() }} disabled={deleteMutation.isPending}>
              <Trash2 className="h-4 w-4 mr-1" /> Delete
            </Button>
          </div>
        }
      />

      <div className="flex flex-wrap items-center gap-2">
        <ApplicationStatusBadge status={application.status} />
        <ApplicationPriorityBadge priority={application.priority} />
        <Badge variant="outline" className="text-muted-foreground">
          <Clock className="h-3 w-3 mr-1" /> {age.label}
        </Badge>
        {badges.map(b => (
          <Badge key={b.type} variant={b.variant}>{b.label}</Badge>
        ))}
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="documents">Documents</TabsTrigger>
          <TabsTrigger value="notes">Notes</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6 mt-6">
          {hasStrategyInfo && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Wand2 className="h-5 w-5 text-primary" />
                  AI Resume Strategy
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {application.resume_strategy && (
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">{strategyLabels[application.resume_strategy] || application.resume_strategy}</Badge>
                    {application.tailored && <Badge variant="outline">Tailored</Badge>}
                    {application.generated && (
                      <Badge variant="outline" className="text-primary">
                        <Sparkles className="h-3 w-3 mr-1" /> AI Generated
                      </Badge>
                    )}
                  </div>
                )}
                {application.original_resume_id && (
                  <div>
                    <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Source resume</p>
                    <p className="text-xs font-mono text-muted-foreground">{application.original_resume_id}</p>
                  </div>
                )}
                {application.generated_resume_id && (
                  <div>
                    <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Generated resume</p>
                    <p className="text-xs font-mono text-muted-foreground">{application.generated_resume_id}</p>
                  </div>
                )}
                {application.generation_timestamp && (
                  <div>
                    <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Generated</p>
                    <p className="text-sm">{new Date(application.generation_timestamp).toLocaleString()}</p>
                  </div>
                )}
                {application.generated && (
                  <p className="text-xs text-muted-foreground flex items-center gap-1">
                    <Recycle className="h-3.5 w-3.5" />
                    Generated resumes are kept only per your AI settings (saved when submitted by default).
                  </p>
                )}
              </CardContent>
            </Card>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Job Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Company</p>
                    <p className="text-sm flex items-center gap-1">
                      <Building2 className="h-3.5 w-3.5 text-muted-foreground" />
                      {application.company_name}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Location</p>
                    <InlineEdit
                      value={application.location || ''}
                      onSave={(v: string) => handleFieldUpdate('location', v)}
                      placeholder="Add location"
                    />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Salary</p>
                    <InlineEdit
                      value={application.salary || ''}
                      onSave={(v: string) => handleFieldUpdate('salary', v)}
                      placeholder="Add salary"
                    />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Deadline</p>
                    <InlineEdit
                      value={application.deadline || ''}
                      onSave={(v: string) => handleFieldUpdate('deadline', v)}
                      placeholder="Set deadline"
                      type="date"
                    />
                  </div>
                  {application.work_type && (
                    <div>
                      <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Work Type</p>
                      <p className="text-sm flex items-center gap-1">
                        <Briefcase className="h-3.5 w-3.5 text-muted-foreground" />
                        {application.work_type}
                      </p>
                    </div>
                  )}
                  {application.source && (
                    <div>
                      <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Source</p>
                      <p className="text-sm flex items-center gap-1">
                        <Globe className="h-3.5 w-3.5 text-muted-foreground" />
                        {application.source}
                      </p>
                    </div>
                  )}
                  <div>
                    <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Recruiter</p>
                    <InlineEdit
                      value={application.recruiter || ''}
                      onSave={(v: string) => handleFieldUpdate('recruiter', v)}
                      placeholder="Add recruiter"
                    />
                  </div>
                </div>
                {application.referral && (
                  <div>
                    <Badge variant="secondary">Referral</Badge>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Update Status</p>
                  <Select
                    value={application.status}
                    onChange={(e) => handleStatusChange(e.target.value)}
                    disabled={updateMutation.isPending}
                    aria-label="Update status"
                  >
                    <option value={application.status}>{getStatusLabel(application.status)} (current)</option>
                    {allowedStatuses.length > 0 ? (
                      allowedStatuses.map(s => (
                        <option key={s} value={s}>{getStatusLabel(s)}</option>
                      ))
                    ) : (
                      <option value="" disabled>No transitions available</option>
                    )}
                  </Select>
                  {statusError && (
                    <p className="text-xs text-error flex items-center gap-1 mt-1" role="alert">
                      <AlertCircle className="h-3 w-3" /> {statusError}
                    </p>
                  )}
                  {allowedStatuses.length === 0 && !statusError && (
                    <p className="text-xs text-muted-foreground mt-1">Final status - no further transitions.</p>
                  )}
                </div>

                <Separator />

                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Update Priority</p>
                  <Select
                    value={application.priority}
                    onChange={(e) => handleStatusChange(e.target.value)}
                    disabled={updateMutation.isPending}
                    aria-label="Update priority"
                  >
                    {PRIORITY_ORDER.map(p => (
                      <option key={p} value={p}>{PRIORITY_LABELS[p]}</option>
                    ))}
                  </Select>
                </div>

                <Separator />

                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Created</p>
                  <p className="text-sm">{new Date(application.created_at).toLocaleDateString()}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Updated</p>
                  <p className="text-sm">{new Date(application.updated_at).toLocaleDateString()}</p>
                </div>
                {application.applied_date && (
                  <div>
                    <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Applied</p>
                    <p className="text-sm">{new Date(application.applied_date).toLocaleDateString()}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="timeline" className="mt-6">
          <ApplicationTimeline applicationId={application.id} />
        </TabsContent>

        <TabsContent value="documents" className="mt-6">
          <ApplicationDocuments resume={documentRefs.resume} coverLetter={documentRefs.coverLetter} />
        </TabsContent>

        <TabsContent value="notes" className="mt-6">
          <ApplicationNotes applicationId={application.id} />
        </TabsContent>

        <TabsContent value="activity" className="mt-6">
          <ApplicationActivity applicationId={application.id} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
