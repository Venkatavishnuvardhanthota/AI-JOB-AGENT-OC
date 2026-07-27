import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useCreateResume, useGenerateResume, useDuplicateResume } from '@/api/hooks'
import { useToast } from '@/components/ui/toast'
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ResumeWizardProps {
  mode: 'generate' | 'blank' | 'duplicate'
  resumes?: any[]
  onComplete: () => void
}

export function ResumeWizard({ mode, resumes = [], onComplete }: ResumeWizardProps) {
  const createResume = useCreateResume()
  const generateResume = useGenerateResume()
  const duplicateResume = useDuplicateResume()
  const { addToast } = useToast()

  const [title, setTitle] = useState(mode === 'generate' ? 'Generated Resume' : '')
  const [duplicateTarget, setDuplicateTarget] = useState('')
  const [saving, setSaving] = useState(false)

  const handleGenerate = async () => {
    setSaving(true)
    try {
      await generateResume.mutateAsync({
        title: title || 'Generated Resume',
        sections: ['summary', 'experience', 'education', 'skills', 'projects'],
      })
      addToast('Resume generated from profile!', 'success')
      onComplete()
    } catch { addToast('Failed to generate resume', 'error') }
    finally { setSaving(false) }
  }

  const handleCreateBlank = async () => {
    setSaving(true)
    try {
      await createResume.mutateAsync({ title: title.trim() || 'Untitled Resume' })
      addToast('Resume created!', 'success')
      onComplete()
    } catch { addToast('Failed to create resume', 'error') }
    finally { setSaving(false) }
  }

  const handleDuplicate = async () => {
    if (!duplicateTarget) return
    setSaving(true)
    try {
      await duplicateResume.mutateAsync({
        id: duplicateTarget,
        data: { title: title.trim() || 'Duplicated Resume' },
      })
      addToast('Resume duplicated!', 'success')
      onComplete()
    } catch { addToast('Failed to duplicate resume', 'error') }
    finally { setSaving(false) }
  }

  if (mode === 'duplicate') {
    return (
      <div className="space-y-4">
        <p className="text-sm text-muted-foreground">Select a resume to duplicate and give it a new name.</p>
        <div className="space-y-2 max-h-60 overflow-y-auto">
          {resumes.filter(r => !r.archived).map((r) => (
            <button
              key={r.id}
              type="button"
              onClick={() => setDuplicateTarget(r.id)}
              className={cn(
                "w-full text-left rounded-lg border p-3 transition-all hover:bg-white/5",
                duplicateTarget === r.id ? "border-primary bg-primary/5" : "border-glass-border"
              )}
            >
              <p className="text-sm font-medium">{r.title}</p>
              <p className="text-xs text-muted-foreground">v{r.version} · {r.section_count} sections</p>
            </button>
          ))}
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">New Title</label>
          <Input value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Software Engineer Resume (v2)" />
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button onClick={handleDuplicate} disabled={!duplicateTarget || !title.trim() || saving}>
            {saving ? 'Duplicating...' : 'Duplicate'}
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="text-xs text-muted-foreground block mb-1">Resume Title</label>
        <Input value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Software Engineer Resume" />
      </div>

      {mode === 'generate' && (
        <div>
          <label className="text-xs text-muted-foreground block mb-2">Included Sections (from profile)</label>
          <div className="space-y-1 text-sm text-muted-foreground">
            {['Summary', 'Experience', 'Education', 'Skills', 'Projects'].map(s => (
              <div key={s} className="flex items-center gap-2">
                <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                <span>{s}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex justify-end gap-2 pt-2">
        <Button
          onClick={mode === 'generate' ? handleGenerate : handleCreateBlank}
          disabled={!title.trim() || saving}
        >
          {saving ? <><Loader2 className="h-4 w-4 mr-1 animate-spin" /> Creating...</> : `Create Resume`}
        </Button>
      </div>
    </div>
  )
}
