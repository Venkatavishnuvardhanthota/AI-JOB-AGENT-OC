import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useJobs, useResumes, useGenerateCoverLetter } from '@/api/hooks'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { useToast } from '@/components/ui/toast'
import { cn } from '@/lib/utils'
import { Loader2, CheckCircle2, FileText, Target, User, Settings, Sparkles } from 'lucide-react'

const WRITING_STYLES = [
  { id: 'professional', label: 'Professional', desc: 'Formal, confident, and engaging' },
  { id: 'technical', label: 'Technical', desc: 'Highlight technologies and methodologies' },
  { id: 'executive', label: 'Executive', desc: 'Leadership, strategy, and business impact' },
  { id: 'friendly', label: 'Friendly', desc: 'Warm and approachable' },
  { id: 'concise', label: 'Concise', desc: 'Brief and direct' },
  { id: 'graduate', label: 'Graduate', desc: 'Early-career focused' },
  { id: 'career_change', label: 'Career Change', desc: 'Transferable skills emphasis' },
]

type Step = 'job' | 'resume' | 'style' | 'options' | 'preview'

export function CoverLetterWizard({ onComplete }: { onComplete: () => void }) {
  const navigate = useNavigate()
  const { data: jobs } = useJobs() as any
  const { data: resumes } = useResumes() as any
  const generateCoverLetter = useGenerateCoverLetter()
  const { addToast } = useToast()
  const [step, setStep] = useState<Step>('job')
  const [selectedJobId, setSelectedJobId] = useState('')
  const [selectedResumeId, setSelectedResumeId] = useState('')
  const [style, setStyle] = useState('professional')
  const [hiringManager, setHiringManager] = useState('')
  const [additionalNotes, setAdditionalNotes] = useState('')
  const [generating, setGenerating] = useState(false)

  const jobList = (jobs as any) || []
  const resumeList = (resumes as any) || []

  const handleGenerate = async () => {
    if (!selectedJobId || !selectedResumeId) return
    setGenerating(true)
    try {
      const result = await generateCoverLetter.mutateAsync({
        job_id: selectedJobId,
        resume_id: selectedResumeId,
        tone: style,
        hiring_manager: hiringManager || undefined,
        additional_notes: additionalNotes || undefined,
      })
      addToast('Cover letter generated!', 'success')
      if ((result as any)?.id) navigate(`/cover-letters/${(result as any).id}`)
      onComplete()
    } catch {
      addToast('Failed to generate cover letter', 'error')
    } finally {
      setGenerating(false)
    }
  }

  const steps = [
    { id: 'job' as Step, label: 'Select Job', icon: Target },
    { id: 'resume' as Step, label: 'Select Resume', icon: FileText },
    { id: 'style' as Step, label: 'Writing Style', icon: User },
    { id: 'options' as Step, label: 'Options', icon: Settings },
    { id: 'preview' as Step, label: 'Generate', icon: Sparkles },
  ]

  const currentIdx = steps.findIndex(s => s.id === step)

  return (
    <div className="space-y-6" role="region" aria-label="Cover letter generation wizard">
      <div className="flex items-center gap-3">
        {steps.map((s, i) => (
          <div key={s.id} className="flex items-center gap-2">
            <div className={cn(
              'flex h-8 w-8 items-center justify-center rounded-full text-xs font-medium transition-colors',
              i < currentIdx ? 'bg-success text-white' : i === currentIdx ? 'bg-accent text-white' : 'bg-dark-700 text-muted-foreground'
            )}>
              {i < currentIdx ? <CheckCircle2 className="h-4 w-4" /> : <s.icon className="h-4 w-4" />}
            </div>
            <span className={cn('text-xs hidden md:inline', i === currentIdx ? 'text-foreground' : 'text-muted-foreground')}>
              {s.label}
            </span>
            {i < steps.length - 1 && <div className="h-px w-4 bg-dark-700 hidden md:block" />}
          </div>
        ))}
      </div>

      {step === 'job' && (
        <div className="space-y-3">
          <h3 className="font-semibold">Select a Job</h3>
          {jobList.length === 0 && <p className="text-sm text-muted-foreground">No saved jobs found.</p>}
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {jobList.map((job: any) => (
              <button
                key={job.id}
                type="button"
                onClick={() => setSelectedJobId(job.id)}
                className={cn(
                  'w-full text-left rounded-lg border p-3 transition-all hover:bg-white/5',
                  selectedJobId === job.id ? 'border-accent bg-accent/5' : 'border-glass-border'
                )}
              >
                <p className="text-sm font-medium">{job.title || job.name}</p>
                <p className="text-xs text-muted-foreground">{job.company}</p>
              </button>
            ))}
          </div>
          <div className="flex justify-end">
            <Button onClick={() => setStep('resume')} disabled={!selectedJobId}>Continue</Button>
          </div>
        </div>
      )}

      {step === 'resume' && (
        <div className="space-y-3">
          <h3 className="font-semibold">Select a Resume</h3>
          {resumeList.length === 0 && <p className="text-sm text-muted-foreground">No resumes found.</p>}
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {resumeList.map((r: any) => (
              <button
                key={r.id}
                type="button"
                onClick={() => setSelectedResumeId(r.id)}
                className={cn(
                  'w-full text-left rounded-lg border p-3 transition-all hover:bg-white/5',
                  selectedResumeId === r.id ? 'border-accent bg-accent/5' : 'border-glass-border'
                )}
              >
                <p className="text-sm font-medium">{r.title || 'Untitled Resume'}</p>
                <p className="text-xs text-muted-foreground">v{r.version} · {r.section_count} sections{r.template && ` · ${r.template}`}</p>
              </button>
            ))}
          </div>
          <div className="flex justify-between">
            <Button variant="ghost" onClick={() => setStep('job')}>Back</Button>
            <Button onClick={() => setStep('style')} disabled={!selectedResumeId}>Continue</Button>
          </div>
        </div>
      )}

      {step === 'style' && (
        <div className="space-y-3">
          <h3 className="font-semibold">Select Writing Style</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {WRITING_STYLES.map(s => (
              <button
                key={s.id}
                type="button"
                onClick={() => setStyle(s.id)}
                className={cn(
                  'rounded-lg border p-4 text-left transition-all hover:bg-white/5',
                  style === s.id ? 'border-accent bg-accent/5' : 'border-glass-border'
                )}
              >
                <p className="text-sm font-medium">{s.label}</p>
                <p className="text-xs text-muted-foreground mt-1">{s.desc}</p>
              </button>
            ))}
          </div>
          <div className="flex justify-between">
            <Button variant="ghost" onClick={() => setStep('resume')}>Back</Button>
            <Button onClick={() => setStep('options')}>Continue</Button>
          </div>
        </div>
      )}

      {step === 'options' && (
        <div className="space-y-4">
          <h3 className="font-semibold">Optional Details</h3>
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Hiring Manager Name</label>
            <Input value={hiringManager} onChange={e => setHiringManager(e.target.value)} placeholder="e.g. John Smith" />
          </div>
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Additional Notes</label>
            <textarea
              className="w-full rounded-md border border-glass-border bg-dark-800 px-3 py-2 text-sm text-foreground min-h-[100px]"
              value={additionalNotes}
              onChange={e => setAdditionalNotes(e.target.value)}
              placeholder="Any specific points you'd like to highlight..."
            />
          </div>
          <div className="flex justify-between">
            <Button variant="ghost" onClick={() => setStep('style')}>Back</Button>
            <Button onClick={() => setStep('preview')}>Review & Generate</Button>
          </div>
        </div>
      )}

      {step === 'preview' && (
        <Card>
          <CardContent className="p-6 text-center space-y-4">
            <Sparkles className="h-12 w-12 mx-auto text-accent" />
            <h3 className="font-semibold">Ready to Generate</h3>
            <p className="text-sm text-muted-foreground">
              An AI-powered cover letter will be generated for the selected job and resume.
              You can edit it after generation.
            </p>
            <div className="flex justify-center gap-3">
              <Button variant="outline" onClick={() => setStep('options')}>Back</Button>
              <Button onClick={handleGenerate} disabled={generating}>
                {generating ? <><Loader2 className="h-4 w-4 mr-1 animate-spin" /> Generating...</> : 'Generate Cover Letter'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
