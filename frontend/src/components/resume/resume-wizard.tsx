import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useGenerateResume } from '@/api/hooks'
import { useToast } from '@/components/ui/toast'
import { Loader2 } from 'lucide-react'

interface ResumeWizardProps {
  onComplete: () => void
}

export function ResumeWizard({ onComplete }: ResumeWizardProps) {
  const generateResume = useGenerateResume()
  const { addToast } = useToast()

  const [title, setTitle] = useState('Generated Resume')
  const [enhanceWithAi, setEnhanceWithAi] = useState(false)
  const [saving, setSaving] = useState(false)

  const handleGenerate = async () => {
    setSaving(true)
    try {
      await generateResume.mutateAsync({
        title: title.trim() || 'Generated Resume',
        sections: ['summary', 'experience', 'education', 'skills', 'projects'],
        enhance_with_ai: enhanceWithAi,
      })
      addToast('Resume generated from profile!', 'success')
      onComplete()
    } catch { addToast('Failed to generate resume', 'error') }
    finally { setSaving(false) }
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="text-xs text-muted-foreground block mb-1">Resume Title</label>
        <Input value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Software Engineer Resume" />
      </div>

      <div>
        <label className="text-xs text-muted-foreground block mb-2">Included Sections (from career profile)</label>
        <div className="space-y-1 text-sm text-muted-foreground">
          {['Summary', 'Experience', 'Education', 'Skills', 'Projects'].map(s => (
            <div key={s} className="flex items-center gap-2">
              <div className="h-1.5 w-1.5 rounded-full bg-primary" />
              <span>{s}</span>
            </div>
          ))}
        </div>
      </div>

      <label className="flex items-start gap-2 text-sm cursor-pointer">
        <input
          type="checkbox"
          checked={enhanceWithAi}
          onChange={e => setEnhanceWithAi(e.target.checked)}
          className="mt-0.5"
        />
        <span>
          Enhance with AI
          <span className="block text-xs text-muted-foreground">Rewrite sections for grammar, tone, action verbs, and keywords using your connected AI provider.</span>
        </span>
      </label>

      <div className="flex justify-end gap-2 pt-2">
        <Button onClick={handleGenerate} disabled={saving}>
          {saving ? <><Loader2 className="h-4 w-4 mr-1 animate-spin" /> Generating...</> : 'Generate Resume'}
        </Button>
      </div>
    </div>
  )
}
