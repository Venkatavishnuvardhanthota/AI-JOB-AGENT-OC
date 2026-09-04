import { useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useResume, useResumeSections, useCreateResumeSection, useUpdateResumeSection, useDeleteResumeSection, useUpdateResume, useReorderSections, useDownloadResume } from '@/api/hooks'
import { ExportPreviewModal } from '@/components/cover-letter/export-preview-modal'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useToast } from '@/components/ui/toast'
import { cn } from '@/lib/utils'
import { AtsScore } from '@/components/resume/ats-score'
import { ResumeHealth } from '@/components/resume/resume-health'
import { ResumeOptimize } from '@/components/resume/resume-optimize'
import {
  ArrowLeft, Plus, Pencil, Trash2, Save, FileText,
  Sparkles, TrendingUp, Heart, Download, Eye, GripVertical,
} from 'lucide-react'

const SECTION_TYPES = [
  'summary', 'experience', 'education', 'skills', 'projects',
  'certifications', 'languages', 'publications', 'awards', 'links', 'custom',
]

export function ResumeDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: resume, isLoading } = useResume(id!)
  const { data: sections, isLoading: sectionsLoading } = useResumeSections(id!)
  const createSection = useCreateResumeSection(id!)
  const updateSection = useUpdateResumeSection(id!)
  const deleteSection = useDeleteResumeSection(id!)
  const updateResume = useUpdateResume()
  const reorderSections = useReorderSections(id!)
  const downloadResume = useDownloadResume()
  const { addToast } = useToast()
  const [activeTab, setActiveTab] = useState('editor')
  const [editingTitle, setEditingTitle] = useState(false)
  const [title, setTitle] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [showExportPreview, setShowExportPreview] = useState(false)
  const [editingSection, setEditingSection] = useState<any | null>(null)
  const [sectionType, setSectionType] = useState('summary')
  const [sectionTitle, setSectionTitle] = useState('')
  const [sectionContent, setSectionContent] = useState('')
  const [dragIdx, setDragIdx] = useState<number | null>(null)

  const handleSaveTitle = useCallback(async () => {
    if (!title.trim()) return
    try {
      await updateResume.mutateAsync({ id: id!, data: { title: title.trim() } })
      addToast('Title updated', 'success')
      setEditingTitle(false)
    } catch { addToast('Failed to update title', 'error') }
  }, [title, id, updateResume, addToast])

  const handleSaveSection = useCallback(async () => {
    if (!sectionType) return
    try {
      const payload: any = { section_type: sectionType, sort_order: 0 }
      if (sectionTitle.trim()) payload.title = sectionTitle.trim()
      if (sectionContent.trim()) payload.content = { text: sectionContent.trim() }

      if (editingSection) {
        await updateSection.mutateAsync({ sectionId: editingSection.id, data: payload })
        addToast('Section updated', 'success')
      } else {
        await createSection.mutateAsync(payload)
        addToast('Section added', 'success')
      }
      resetForm()
    } catch { addToast('Failed to save section', 'error') }
  }, [sectionType, sectionTitle, sectionContent, editingSection, createSection, updateSection, addToast])

  const handleEditSection = useCallback((section: any) => {
    setEditingSection(section)
    setSectionType(section.section_type)
    setSectionTitle(section.title || '')
    setSectionContent(section.content?.text || '')
    setShowForm(true)
  }, [])

  const handleDeleteSection = useCallback(async (sectionId: string) => {
    try { await deleteSection.mutateAsync(sectionId); addToast('Section deleted', 'info') }
    catch { addToast('Failed to delete section', 'error') }
  }, [deleteSection, addToast])

  const handleDownloadPdf = useCallback(async () => {
    try { await downloadResume.mutateAsync({ id: id!, format: 'pdf' }) }
    catch { addToast('Failed to download', 'error') }
  }, [id, downloadResume, addToast])

  const handleDownloadDocx = useCallback(async () => {
    try { await downloadResume.mutateAsync({ id: id!, format: 'docx' }) }
    catch { addToast('Failed to download', 'error') }
  }, [id, downloadResume, addToast])

  const resetForm = useCallback(() => {
    setShowForm(false)
    setEditingSection(null)
    setSectionType('summary')
    setSectionTitle('')
    setSectionContent('')
  }, [])

  const sortedSections = ((sections as any) || []).slice().sort((a: any, b: any) => a.sort_order - b.sort_order)

  const handleDragStart = useCallback((e: React.DragEvent, idx: number) => {
    setDragIdx(idx)
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', String(idx))
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }, [])

  const handleDrop = useCallback(async (e: React.DragEvent, dropIdx: number) => {
    e.preventDefault()
    if (dragIdx === null || dragIdx === dropIdx) { setDragIdx(null); return }
    const copy = [...sortedSections]
    const [moved] = copy.splice(dragIdx, 1)
    copy.splice(dropIdx, 0, moved)
    const newOrder = copy.map((s: any, i: number) => ({ section_id: s.id, sort_order: i }))
    try {
      await reorderSections.mutateAsync(newOrder)
      addToast('Section reordered', 'success')
    } catch { addToast('Failed to reorder', 'error') }
    setDragIdx(null)
  }, [dragIdx, sortedSections, reorderSections, addToast])

  const handleDragEnd = useCallback(() => { setDragIdx(null) }, [])

  if (isLoading) return (
    <div className="space-y-6 max-w-4xl">
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-64 rounded-xl" />
    </div>
  )

  if (!resume) return (
    <div className="text-center py-16 text-muted-foreground">
      <p className="text-lg mb-2">Resume not found</p>
      <Button variant="outline" asChild><Link to="/resumes">Back to Resume Library</Link></Button>
    </div>
  )

  return (
    <div className="space-y-6 max-w-4xl">
      <Link to="/resumes" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-2">
        <ArrowLeft className="h-4 w-4" /> Back to Resume Library
      </Link>

      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div className="space-y-1 flex-1 min-w-0">
          {editingTitle ? (
            <div className="flex items-center gap-2">
              <Input value={title} onChange={e => setTitle(e.target.value)} className="text-xl font-bold h-10" autoFocus />
              <Button size="sm" onClick={handleSaveTitle} disabled={updateResume.isPending}>
                <Save className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setEditingTitle(false)}>Cancel</Button>
            </div>
          ) : (
            <h1
              className="text-2xl font-bold text-foreground cursor-pointer hover:text-primary transition-colors truncate"
              onClick={() => { setTitle(resume.title || ''); setEditingTitle(true) }}
              role="button"
              tabIndex={0}
              aria-label="Edit resume title"
            >
              {resume.title || 'Untitled Resume'}
            </h1>
          )}
          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <span>v{resume.version}</span>
            <Badge variant={resume.status === 'active' || resume.status === 'complete' ? 'success' : 'warning'} className="text-xs">{resume.status}</Badge>
          </div>
        </div>
        <div className="flex flex-wrap gap-2 shrink-0">
          <Button variant="outline" size="sm" onClick={() => setShowExportPreview(true)} aria-label="Preview and export">
            <Eye className="h-4 w-4 mr-1" /> Preview
          </Button>
          <Button variant="outline" size="sm" onClick={handleDownloadPdf} aria-label="Download as PDF">
            <Download className="h-4 w-4 mr-1" /> PDF
          </Button>
          <Button variant="outline" size="sm" onClick={handleDownloadDocx} aria-label="Download as DOCX">
            <Download className="h-4 w-4 mr-1" /> DOCX
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="flex-wrap">
          <TabsTrigger value="editor" aria-controls="tab-editor">
            <FileText className="h-4 w-4 mr-1" /> Editor
          </TabsTrigger>
          <TabsTrigger value="ats" aria-controls="tab-ats">
            <TrendingUp className="h-4 w-4 mr-1" /> ATS
          </TabsTrigger>
          <TabsTrigger value="health" aria-controls="tab-health">
            <Heart className="h-4 w-4 mr-1" /> Health
          </TabsTrigger>
          <TabsTrigger value="optimize" aria-controls="tab-optimize">
            <Sparkles className="h-4 w-4 mr-1" /> Optimize
          </TabsTrigger>
        </TabsList>

        <TabsContent value="editor" className="mt-6" id="tab-editor">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">
                  Sections
                  {!sectionsLoading && <span className="text-muted-foreground font-normal ml-1">({sortedSections.length})</span>}
                </h2>
                <Button variant="outline" size="sm" onClick={() => { resetForm(); setShowForm(true) }}>
                  <Plus className="h-4 w-4 mr-1" /> Add Section
                </Button>
              </div>

              {sectionsLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map(i => <Skeleton key={i} className="h-16 w-full rounded-lg" />)}
                </div>
              ) : sortedSections.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No sections yet. Click "Add Section" to start building your resume.
                </p>
              ) : (
                <div className="space-y-2">
                  {sortedSections.map((section: any, index: number) => (
                    <div
                      key={section.id}
                      draggable
                      onDragStart={(e) => handleDragStart(e, index)}
                      onDragOver={handleDragOver}
                      onDrop={(e) => handleDrop(e, index)}
                      onDragEnd={handleDragEnd}
                      className={cn(
                        'flex items-start gap-2 group',
                        dragIdx === index && 'opacity-40'
                      )}
                    >
                      <div className="flex flex-col gap-0.5 pt-2 cursor-grab active:cursor-grabbing">
                        <GripVertical className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                      <div className={cn(
                        'flex-1 rounded-lg border p-3 transition-colors',
                        dragIdx !== null && dragIdx !== index ? 'border-primary/40 bg-primary/5' : 'border-glass-border group-hover:border-primary/30'
                      )}>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3 min-w-0">
                            <FileText className="h-5 w-5 text-primary shrink-0" />
                            <div className="min-w-0">
                              <div className="flex items-center gap-2">
                                <p className="text-sm font-medium">{section.title || section.section_type}</p>
                                <Badge variant="outline" className="text-[10px]">{section.section_type}</Badge>
                              </div>
                              {section.content?.text && (
                                <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2 whitespace-pre-wrap">{section.content.text}</p>
                              )}
                            </div>
                          </div>
                          <div className="flex gap-1 shrink-0">
                            <Button variant="ghost" size="sm" onClick={() => handleEditSection(section)} aria-label="Edit section">
                              <Pencil className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => handleDeleteSection(section.id)} aria-label="Delete section">
                              <Trash2 className="h-4 w-4 text-error" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ats" className="mt-6" id="tab-ats">
          <AtsScore resumeId={id!} />
        </TabsContent>

        <TabsContent value="health" className="mt-6" id="tab-health">
          <ResumeHealth resumeId={id!} />
        </TabsContent>

        <TabsContent value="optimize" className="mt-6" id="tab-optimize">
          <ResumeOptimize
            resumeId={id!}
            resumeTitle={resume.title || 'Resume'}
            onOptimized={() => setActiveTab('editor')}
          />
        </TabsContent>
      </Tabs>

      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={resetForm}>
          <div className="bg-dark-900 border border-glass-border rounded-xl p-6 w-[32rem]" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">{editingSection ? 'Edit' : 'Add'} Section</h3>
            <div className="space-y-4">
              <div>
                <label className="text-xs text-muted-foreground block mb-1">Section Type</label>
                <select
                  className="w-full rounded-md border border-glass-border bg-dark-800 px-3 py-2 text-sm text-foreground"
                  value={sectionType}
                  onChange={e => setSectionType(e.target.value)}
                >
                  {SECTION_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-muted-foreground block mb-1">Title</label>
                <Input value={sectionTitle} onChange={e => setSectionTitle(e.target.value)} placeholder="e.g. Software Engineering Intern" />
              </div>
              <div>
                <label className="text-xs text-muted-foreground block mb-1">Content</label>
                <textarea
                  className="w-full rounded-md border border-glass-border bg-dark-800 px-3 py-2 text-sm text-foreground min-h-[180px]"
                  value={sectionContent}
                  onChange={e => setSectionContent(e.target.value)}
                  placeholder="Describe this section..."
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-4">
              <Button variant="outline" onClick={resetForm}>Cancel</Button>
              <Button onClick={handleSaveSection} disabled={createSection.isPending || updateSection.isPending}>
                {editingSection ? 'Update' : 'Add'}
              </Button>
            </div>
          </div>
        </div>
      )}

      <ExportPreviewModal
        open={showExportPreview}
        onClose={() => setShowExportPreview(false)}
        content={sortedSections.map((s: any) =>
          `<div style="margin-bottom:12px"><strong>${s.title || s.section_type}</strong><p>${s.content?.text || ''}</p></div>`
        ).join('')}
        title={resume.title || 'Resume'}
        onExport={async (format: string) => {
          if (format === 'pdf') await handleDownloadPdf()
          else await handleDownloadDocx()
        }}
      />
    </div>
  )
}
