import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { useToast } from '@/components/ui/toast'
import { useResumeStrategy, useUpdateResumeStrategy } from '@/api/hooks'
import type { ResumeStrategyOption, SaveGeneratedResumesOption } from '@/types'
import { Save, Loader2, Wand2, CheckCircle2 } from 'lucide-react'

const STRATEGY_LABELS: Record<ResumeStrategyOption, string> = {
  use_existing: 'Use Best Resume',
  tailor: 'Tailor Best Resume (Recommended)',
  generate: 'Generate New Resume',
  ask: 'Ask Me Each Time',
}

const STRATEGY_DESCRIPTIONS: Record<ResumeStrategyOption, string> = {
  use_existing:
    'Reuse the master resume that fits the job best. Zero AI credits, fastest path to apply.',
  tailor:
    'Copy your best master resume and have AI tailor it to the job description. Balances quality and AI credit usage.',
  generate:
    'Generate a fresh resume from your career profile, optimized for the job. Best match, highest AI credit usage.',
  ask: 'Preview the recommended resume and strategy before every application and choose at that time.',
}

const SAVE_LABELS: Record<SaveGeneratedResumesOption, string> = {
  never: 'Never Keep',
  submitted_only: 'Keep When Submitted (Recommended)',
  every: 'Always Keep',
}

const SAVE_DESCRIPTIONS: Record<SaveGeneratedResumesOption, string> = {
  never: 'Discard AI-generated resumes after the application is finished.',
  submitted_only:
    'Keep AI-generated resumes only for applications you submit. Discarded ones are deleted to avoid clutter.',
  every: 'Keep every AI-generated resume, even for applications you never submit.',
}

export function ResumeStrategySettings() {
  const { addToast } = useToast()
  const { data, isLoading } = useResumeStrategy()
  const update = useUpdateResumeStrategy()
  const [strategy, setStrategy] = useState<ResumeStrategyOption>('tailor')
  const [save, setSave] = useState<SaveGeneratedResumesOption>('submitted_only')
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (data) {
      setStrategy(data.resume_strategy)
      setSave(data.save_generated_resumes)
    }
  }, [data])

  const handleSave = () => {
    update.mutate(
      { resume_strategy: strategy, save_generated_resumes: save },
      {
        onSuccess: () => {
          setSaved(true)
          addToast('Resume strategy updated', 'success')
          setTimeout(() => setSaved(false), 3000)
        },
        onError: (err: Error) => addToast(`Save failed: ${err.message}`, 'error'),
      },
    )
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle><Skeleton className="h-5 w-48" /></CardTitle></CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3].map(i => <Skeleton key={i} className="h-9 w-full" />)}
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Wand2 className="h-5 w-5 text-primary" />
          Resume Strategy
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <label className="text-xs text-muted-foreground mb-1 block">When preparing an application</label>
          <Select value={strategy} onChange={e => setStrategy(e.target.value as ResumeStrategyOption)}>
            {(Object.keys(STRATEGY_LABELS) as ResumeStrategyOption[]).map(option => (
              <option key={option} value={option}>{STRATEGY_LABELS[option]}</option>
            ))}
          </Select>
          <p className="text-xs text-muted-foreground mt-2">{STRATEGY_DESCRIPTIONS[strategy]}</p>
        </div>

        <div>
          <label className="text-xs text-muted-foreground mb-1 block">AI-generated resumes</label>
          <Select value={save} onChange={e => setSave(e.target.value as SaveGeneratedResumesOption)}>
            {(Object.keys(SAVE_LABELS) as SaveGeneratedResumesOption[]).map(option => (
              <option key={option} value={option}>{SAVE_LABELS[option]}</option>
            ))}
          </Select>
          <p className="text-xs text-muted-foreground mt-2">{SAVE_DESCRIPTIONS[save]}</p>
        </div>

        {saved && (
          <div className="flex items-center gap-1 text-sm text-success">
            <CheckCircle2 className="h-4 w-4" />
            Resume strategy saved successfully
          </div>
        )}

        <div>
          <Button onClick={handleSave} disabled={update.isPending}>
            {update.isPending ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Save className="h-4 w-4 mr-1" />}
            Save Strategy
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
