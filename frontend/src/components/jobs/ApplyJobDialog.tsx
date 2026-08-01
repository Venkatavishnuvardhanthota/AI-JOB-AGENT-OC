import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useToast } from '@/components/ui/toast'
import { useResumeStrategyPreview, useResumeStrategySelect } from '@/api/hooks'
import type { ResumeStrategyOption } from '@/types'
import { Loader2, Wand2, CheckCircle2, AlertCircle, Recycle, X } from 'lucide-react'

const STRATEGY_LABELS: Record<ResumeStrategyOption, string> = {
  use_existing: 'Use Best Resume',
  tailor: 'Tailor Best Resume',
  generate: 'Generate New Resume',
  ask: 'Ask Me',
}

const STRATEGY_HINTS: Record<ResumeStrategyOption, string> = {
  use_existing: 'Reuse the best-fitting resume. No AI credits.',
  tailor: 'AI tailors your best resume to this job. Uses AI credits.',
  generate: 'AI builds a new resume from your profile. Uses AI credits.',
  ask: 'Let me decide now.',
}

interface ApplyJobDialogProps {
  jobId: string
  jobTitle?: string
  companyName?: string
  open: boolean
  onClose: () => void
  onCompleted?: () => void
}

export function ApplyJobDialog({ jobId, jobTitle, companyName, open, onClose, onCompleted }: ApplyJobDialogProps) {
  const { addToast } = useToast()
  const { data: preview, isLoading: previewLoading, isError } = useResumeStrategyPreview(jobId)
  const select = useResumeStrategySelect()
  const [strategy, setStrategy] = useState<ResumeStrategyOption | null>(null)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (open) {
      setResult(null)
      setError('')
      setStrategy(null)
    }
  }, [open])

  useEffect(() => {
    if (preview && strategy === null) {
      setStrategy(preview.recommended_strategy)
    }
  }, [preview, strategy])

  if (!open) return null

  const handleConfirm = () => {
    if (!strategy) return
    setError('')
    select.mutate(
      { job_id: jobId, strategy_override: strategy, generate_cover_letter: true },
      {
        onSuccess: (data: any) => {
          if (data?.needs_choice) {
            setError('Please choose a strategy to continue.')
            return
          }
          setResult(data)
          addToast('Application prepared', 'success')
          onCompleted?.()
        },
        onError: (err: Error) => {
          const message = err.message || 'Failed to prepare application'
          if (message.includes('already exists')) {
            setError('You already have an application for this job.')
          } else if (message.includes('resume')) {
            setError('No suitable resume found. Add a resume in the Resume Library first.')
          } else {
            setError(message)
          }
        },
      },
    )
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Apply with AI"
    >
      <div
        className="bg-dark-900 border border-glass-border rounded-xl w-full max-w-xl max-h-[85vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-start justify-between p-6 pb-2">
          <div>
            <h2 className="text-xl font-semibold">Apply with AI</h2>
            <p className="text-sm text-muted-foreground mt-1">
              {jobTitle}{companyName ? ` at ${companyName}` : ''}
            </p>
          </div>
          <button type="button" onClick={onClose} className="text-muted-foreground hover:text-foreground" aria-label="Close">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 pt-2 space-y-5">
          {previewLoading && (
            <div className="space-y-3">
              <Skeleton className="h-5 w-2/3" />
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          )}

          {isError && (
            <div className="text-center py-8">
              <AlertCircle className="h-10 w-10 text-error mx-auto mb-2" />
              <p className="text-sm text-error">Could not analyze this job for resume selection.</p>
            </div>
          )}

          {preview && !previewLoading && (
            <>
              {preview.reused_generated && preview.generated_resume_title && (
                <div className="flex items-center gap-2 text-sm text-primary bg-primary/10 rounded-lg px-3 py-2">
                  <Recycle className="h-4 w-4" />
                  A previously generated resume for this job exists and will be reused — no new AI credits.
                </div>
              )}

              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Recommended strategy</p>
                <p className="text-sm font-medium text-foreground">{preview.rationale}</p>
              </div>

              {preview.selected_resume_id && preview.scores.length > 0 && (
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Resume fit scores</p>
                  <div className="space-y-2">
                    {preview.scores.map((s: any) => (
                      <div
                        key={s.resume_id}
                        className={`flex items-center justify-between rounded-lg border px-3 py-2 text-sm ${
                          s.selected ? 'border-primary/40 bg-primary/5' : 'border-glass-border'
                        }`}
                      >
                        <span className="flex items-center gap-2">
                          <span className="font-medium">{s.title || 'Untitled'}</span>
                          {s.selected && <Badge variant="secondary">Best</Badge>}
                        </span>
                        <span className="text-muted-foreground">
                          {Math.round(s.overall * 100)}% match
                          <span className="ml-2 hidden sm:inline text-xs">skills {Math.round(s.skill_overlap * 100)}%</span>
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Choose how to apply</p>
                <div className="grid grid-cols-1 gap-2">
                  {(['use_existing', 'tailor', 'generate'] as ResumeStrategyOption[]).map(option => (
                    <button
                      key={option}
                      type="button"
                      onClick={() => setStrategy(option)}
                      className={`flex items-start gap-3 rounded-lg border p-3 text-left transition-all ${
                        strategy === option ? 'border-primary/50 bg-primary/10' : 'border-glass-border hover:bg-white/5'
                      }`}
                    >
                      <input
                        type="radio"
                        checked={strategy === option}
                        onChange={() => setStrategy(option)}
                        className="mt-1 accent-[var(--color-primary)]"
                        aria-label={STRATEGY_LABELS[option]}
                      />
                      <span>
                        <span className="block text-sm font-medium">{STRATEGY_LABELS[option]}</span>
                        <span className="block text-xs text-muted-foreground mt-0.5">{STRATEGY_HINTS[option]}</span>
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}

          {error && (
            <div className="flex items-center gap-2 text-sm text-error bg-error/10 rounded-lg px-3 py-2" role="alert">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          {result && (
            <div className="flex items-start gap-2 text-sm text-success bg-success/10 rounded-lg px-3 py-3">
              <CheckCircle2 className="h-5 w-5 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <p className="font-medium">Application ready for review</p>
                <p className="text-xs text-muted-foreground">
                  {result.generated_resume_title
                    ? `Resume: ${result.generated_resume_title}`
                    : result.selected_resume_title
                      ? `Resume: ${result.selected_resume_title}`
                      : ''}
                  {result.reused_generated ? ' (reused — no AI credits spent)' : ''}
                  {result.cover_letter_id ? ' · Cover letter generated' : ''}
                </p>
              </div>
            </div>
          )}

          <div className="flex gap-2 justify-end pt-2">
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
            <Button onClick={handleConfirm} disabled={!strategy || select.isPending || !!result}>
              {select.isPending ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Wand2 className="h-4 w-4 mr-1" />}
              {result ? 'Done' : 'Prepare Application'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
