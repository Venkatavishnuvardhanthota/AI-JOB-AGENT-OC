import { useState } from 'react'
import { useCoverLetters, useResumes, useApplicationPackage } from '@/api/hooks'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/toast'
import { cn } from '@/lib/utils'
import { Loader2, Package, Briefcase, Mail } from 'lucide-react'

interface ApplicationPackageProps {
  jobId: string
  onComplete?: () => void
}

export function ApplicationPackage({ jobId, onComplete }: ApplicationPackageProps) {
  const { data: coverLetters } = useCoverLetters('ready') as any
  const { data: resumes } = useResumes() as any
  const createPackage = useApplicationPackage()
  const { addToast } = useToast()
  const [selectedResumeId, setSelectedResumeId] = useState('')
  const [selectedCoverLetterId, setSelectedCoverLetterId] = useState('')
  const [notes, setNotes] = useState('')
  const [bundling, setBundling] = useState(false)

  const readyLetters = (coverLetters || []).filter((cl: any) => cl.status === 'ready')
  const resumeList = (resumes as any) || []

  const handleCreatePackage = async () => {
    if (!selectedResumeId || !selectedCoverLetterId) return
    setBundling(true)
    try {
      await createPackage.mutateAsync({
        job_id: jobId,
        resume_id: selectedResumeId,
        cover_letter_id: selectedCoverLetterId,
        notes: notes || undefined,
      })
      addToast('Application package created!', 'success')
      onComplete?.()
    } catch {
      addToast('Failed to create application package', 'error')
    } finally {
      setBundling(false)
    }
  }

  return (
    <div className="space-y-6" role="region" aria-label="Create application package">
      <div className="flex items-center gap-3 pb-3 border-b border-glass-border">
        <Package className="h-5 w-5 text-accent" />
        <h3 className="font-semibold">Create Application Package</h3>
      </div>

      <div className="space-y-3">
        <p className="text-sm font-medium flex items-center gap-2">
          <Briefcase className="h-4 w-4" /> Select Resume
        </p>
        {resumeList.length === 0 && <p className="text-sm text-muted-foreground">No resumes available.</p>}
        <div className="space-y-2 max-h-48 overflow-y-auto">
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
              <p className="text-sm font-medium">{r.title || 'Untitled'}</p>
              <p className="text-xs text-muted-foreground">v{r.version} · {r.section_count || 0} sections</p>
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        <p className="text-sm font-medium flex items-center gap-2">
          <Mail className="h-4 w-4" /> Select Cover Letter
        </p>
        {readyLetters.length === 0 && <p className="text-sm text-muted-foreground">No ready cover letters. Generate one first.</p>}
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {readyLetters.map((cl: any) => (
            <button
              key={cl.id}
              type="button"
              onClick={() => setSelectedCoverLetterId(cl.id)}
              className={cn(
                'w-full text-left rounded-lg border p-3 transition-all hover:bg-white/5',
                selectedCoverLetterId === cl.id ? 'border-accent bg-accent/5' : 'border-glass-border'
              )}
            >
              <p className="text-sm font-medium">{cl.title || 'Untitled'}</p>
              <p className="text-xs text-muted-foreground">{cl.company_name ? `${cl.company_name} — ` : ''}{cl.job_title || `v${cl.version}`}</p>
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="text-xs text-muted-foreground block mb-1">Optional Notes</label>
        <textarea
          className="w-full rounded-md border border-glass-border bg-dark-800 px-3 py-2 text-sm min-h-[80px]"
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder="Add any notes for your application package..."
        />
      </div>

      <div className="flex justify-end">
        <Button onClick={handleCreatePackage} disabled={!selectedResumeId || !selectedCoverLetterId || bundling}>
          {bundling ? <><Loader2 className="h-4 w-4 mr-1 animate-spin" /> Creating Package...</> : 'Create Package'}
        </Button>
      </div>
    </div>
  )
}
