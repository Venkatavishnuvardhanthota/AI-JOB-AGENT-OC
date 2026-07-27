import { useState, useCallback, useEffect, lazy, Suspense } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { useToast } from '@/components/ui/toast'
import { useUpdateCoverLetter, useExportCoverLetter } from '@/api/hooks'
import { useAutosave, SaveStatus } from '@/hooks/useAutosave'
import { RichTextEditor, renderToText } from './rich-text-editor'
import { AIInlineEdit } from './ai-inline-edit'
import { ExportPreviewModal } from './export-preview-modal'
import { CompanyIntel } from './company-intel'
import { TemplatePanel } from './template-panel'
import { cn } from '@/lib/utils'
import {
  Loader2, Save, Sparkles, History, Layout,
  CheckCircle2, AlertTriangle, XCircle, Eye,
} from 'lucide-react'

const CoverLetterVersionPanel = lazy(() =>
  import('./cover-letter-version-panel').then(m => ({ default: m.CoverLetterVersionPanel }))
)
const CoverLetterCompare = lazy(() =>
  import('./cover-letter-compare').then(m => ({ default: m.CoverLetterCompare }))
)

interface CoverLetterEditorProps {
  coverLetter: any
  onSaved: () => void
}

const STATUS_CONFIG: Record<SaveStatus, { label: string; icon: any; className: string }> = {
  saved: { label: 'Saved', icon: CheckCircle2, className: 'text-success' },
  saving: { label: 'Saving...', icon: Loader2, className: 'text-accent animate-spin' },
  unsaved: { label: 'Unsaved Changes', icon: AlertTriangle, className: 'text-warning' },
  error: { label: 'Save Failed', icon: XCircle, className: 'text-error' },
}

export function CoverLetterEditor({ coverLetter, onSaved }: CoverLetterEditorProps) {
  const [content, setContent] = useState(coverLetter?.content || '')
  const [title, setTitle] = useState(coverLetter?.title || '')
  const [template, setTemplate] = useState(coverLetter?.template || 'modern')
  const [showExportPreview, setShowExportPreview] = useState(false)
  const [compareContent, setCompareContent] = useState('')
  const [activePanel, setActivePanel] = useState<'edit' | 'version' | 'template' | 'compare'>('edit')

  const updateCoverLetter = useUpdateCoverLetter()
  const exportCoverLetter = useExportCoverLetter()
  const { addToast } = useToast()

  const saveContent = useCallback(async (c: string) => {
    await updateCoverLetter.mutateAsync({ id: coverLetter.id, data: { content: c } })
  }, [coverLetter.id, updateCoverLetter])

  const autosave = useAutosave({ delay: 2000, onSave: saveContent })

  const handleContentChange = useCallback((html: string) => {
    setContent(html)
    const plainText = renderToText(html)
    if (plainText.trim()) autosave.onChange(html)
  }, [autosave])

  const handleSave = useCallback(async () => {
    try {
      await updateCoverLetter.mutateAsync({ id: coverLetter.id, data: { title, content, template } })
      await autosave.saveNow()
      addToast('Cover letter saved', 'success')
      onSaved()
    } catch {
      addToast('Failed to save', 'error')
    }
  }, [coverLetter.id, title, content, template, updateCoverLetter, autosave, addToast, onSaved])

  const handleAiEdit = useCallback((newContent: string) => {
    setContent(newContent)
    setActivePanel('edit')
  }, [])

  const handleRestoreVersion = useCallback((versionContent: string) => {
    setContent(versionContent)
    setActivePanel('edit')
    addToast('Version content loaded in editor', 'success')
  }, [addToast])

  const handleCompare = useCallback((_v: string, b: string) => {
    setCompareContent(b)
    setActivePanel('compare')
  }, [])

  const handleExport = useCallback(async (format: string) => {
    await exportCoverLetter.mutateAsync({ id: coverLetter.id, format })
  }, [coverLetter.id, exportCoverLetter])

  const handleTemplateChange = useCallback((templateId: string) => {
    setTemplate(templateId)
    addToast(`Template changed to ${templateId}`, 'success')
  }, [addToast])

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (autosave.status === 'unsaved') { e.preventDefault(); e.returnValue = '' }
    }
    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [autosave.status])

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); handleSave() }
    }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [handleSave])

  const SaveStatusIcon = STATUS_CONFIG[autosave.status].icon

  const panels = [
    { id: 'edit' as const, label: 'Editor', icon: Sparkles },
    { id: 'version' as const, label: 'Versions', icon: History },
    { id: 'template' as const, label: 'Templates', icon: Layout },
    { id: 'compare' as const, label: 'Compare', icon: Eye },
  ]

  return (
    <div className="space-y-4" role="region" aria-label="Cover letter editor">
      <div className="flex items-center gap-3">
        <div className="flex-1">
          <Input
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="Cover Letter Title"
            className="text-lg font-semibold border-0 px-0"
            aria-label="Cover letter title"
          />
        </div>
        <div className="flex items-center gap-2">
          <span className={cn('text-xs flex items-center gap-1', STATUS_CONFIG[autosave.status].className)}>
            <SaveStatusIcon className="h-3 w-3" />
            {STATUS_CONFIG[autosave.status].label}
          </span>
          <Button variant="outline" size="sm" onClick={() => setShowExportPreview(true)} aria-label="Preview and export">
            <Eye className="h-4 w-4 mr-1" /> Preview
          </Button>
          <Button size="sm" onClick={handleSave} aria-label="Save cover letter">
            <Save className="h-4 w-4 mr-1" /> Save
          </Button>
        </div>
      </div>

      <div className="flex gap-1 p-1 rounded-lg border border-glass-border bg-dark-800/30">
        {panels.map(p => (
          <button
            key={p.id}
            onClick={() => setActivePanel(p.id)}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors',
              activePanel === p.id ? 'bg-accent/10 text-accent' : 'text-muted-foreground hover:text-foreground hover:bg-white/5',
            )}
            aria-pressed={activePanel === p.id}
          >
            <p.icon className="h-3.5 w-3.5" />
            {p.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className={cn('lg:col-span-3', activePanel !== 'edit' && 'hidden lg:block lg:col-span-4')}>
          {activePanel === 'edit' && (
            <div className="space-y-4">
              <RichTextEditor
                value={content}
                onChange={handleContentChange}
                placeholder="Start writing your cover letter..."
              />
              <AIInlineEdit
                coverLetterId={coverLetter.id}
                content={content}
                onApplyEdit={handleAiEdit}
              />
            </div>
          )}

          {activePanel === 'version' && (
            <Suspense fallback={<Skeleton className="h-40 rounded-xl" />}>
              <CoverLetterVersionPanel
                coverLetterId={coverLetter.id}
                currentVersion={coverLetter.version || 1}
                onRestore={handleRestoreVersion}
                onCompare={handleCompare}
              />
            </Suspense>
          )}

          {activePanel === 'template' && (
            <Suspense fallback={<Skeleton className="h-40 rounded-xl" />}>
              <TemplatePanel
                currentTemplate={template}
                onSelect={handleTemplateChange}
              />
            </Suspense>
          )}

          {activePanel === 'compare' && (
            <Suspense fallback={<Skeleton className="h-40 rounded-xl" />}>
              <CoverLetterCompare
                original={coverLetter.content || ''}
                edited={compareContent || content}
                labelA="Saved"
                labelB="Compare"
              />
            </Suspense>
          )}
        </div>

        {activePanel === 'edit' && (
          <div className="space-y-4 lg:col-span-1">
            <CompanyIntel
              jobId={coverLetter.job_id}
              companyName={coverLetter.company_name}
            />
          </div>
        )}
      </div>

      <ExportPreviewModal
        open={showExportPreview}
        onClose={() => setShowExportPreview(false)}
        content={content}
        title={title}
        onExport={handleExport}
      />
    </div>
  )
}

export function CoverLetterEditorPage({ coverLetter, onSaved }: CoverLetterEditorProps) {
  return <CoverLetterEditor coverLetter={coverLetter} onSaved={onSaved} />
}
