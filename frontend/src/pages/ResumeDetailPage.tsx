import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useResume, useResumeSections, useCreateResumeSection, useUpdateResumeSection, useDeleteResumeSection, useUpdateResume, useReorderSections } from '@/api/hooks'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent } from '@/components/ui/card'
import { useToast } from '@/components/ui/toast'
import { ArrowLeft, Plus, Pencil, Trash2, Save, FileText, ArrowUp, ArrowDown, Layout } from 'lucide-react'

const SECTION_TYPES = [
  'summary', 'experience', 'education', 'skills', 'projects',
  'certifications', 'languages', 'publications', 'awards', 'links', 'custom',
]

export function ResumeDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: resume, isLoading } = useResume(id!) as any
  const { data: sections, isLoading: sectionsLoading } = useResumeSections(id!) as any
  const createSection = useCreateResumeSection(id!)
  const updateSection = useUpdateResumeSection(id!)
  const deleteSection = useDeleteResumeSection(id!)
  const updateResume = useUpdateResume()
  const reorderSections = useReorderSections(id!)
  const { addToast } = useToast()

  const [editingTitle, setEditingTitle] = useState(false)
  const [title, setTitle] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingSection, setEditingSection] = useState<any | null>(null)
  const [sectionType, setSectionType] = useState('summary')
  const [sectionTitle, setSectionTitle] = useState('')
  const [sectionContent, setSectionContent] = useState('')

  const handleSaveTitle = async () => {
    if (!title.trim()) return
    try {
      await updateResume.mutateAsync({ id: id!, data: { title: title.trim() } })
      addToast('Title updated', 'success')
      setEditingTitle(false)
    } catch { addToast('Failed to update title', 'error') }
  }

  const handleSaveSection = async () => {
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
  }

  const handleEditSection = (section: any) => {
    setEditingSection(section)
    setSectionType(section.section_type)
    setSectionTitle(section.title || '')
    setSectionContent(section.content?.text || '')
    setShowForm(true)
  }

  const handleDeleteSection = async (sectionId: string) => {
    try { await deleteSection.mutateAsync(sectionId); addToast('Section deleted', 'info') }
    catch { addToast('Failed to delete section', 'error') }
  }

  const handleMoveSection = async (index: number, direction: 'up' | 'down') => {
    const list = sortedSections
    const target = direction === 'up' ? index - 1 : index + 1
    if (target < 0 || target >= list.length) return

    const copy = [...list]
    ;[copy[index], copy[target]] = [copy[target], copy[index]]
    const newOrder = copy.map((s: any, i: number) => ({ section_id: s.id, sort_order: i }))
    try {
      await reorderSections.mutateAsync(newOrder)
      addToast('Section moved', 'success')
    } catch { addToast('Failed to reorder', 'error') }
  }

  const resetForm = () => {
    setShowForm(false)
    setEditingSection(null)
    setSectionType('summary')
    setSectionTitle('')
    setSectionContent('')
  }

  if (isLoading) return (
    <div className="space-y-6 max-w-3xl">
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

  const sortedSections = ((sections as any) || []).slice().sort((a: any, b: any) => a.sort_order - b.sort_order)

  return (
    <div className="space-y-6 max-w-3xl">
      <Link to="/resumes" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-2">
        <ArrowLeft className="h-4 w-4" /> Back to Resume Library
      </Link>

      <div className="flex items-start justify-between">
        <div className="space-y-1">
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
              className="text-2xl font-bold text-foreground cursor-pointer hover:text-primary transition-colors"
              onClick={() => { setTitle(resume.title || ''); setEditingTitle(true) }}
              role="button"
              tabIndex={0}
            >
              {resume.title || 'Untitled Resume'}
            </h1>
          )}
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>v{resume.version}</span>
            <Badge variant={resume.status === 'complete' ? 'success' : 'warning'} className="text-xs">{resume.status}</Badge>
            {resume.template && (
              <Badge variant="secondary" className="text-xs gap-1">
                <Layout className="h-3 w-3" /> {resume.template}
              </Badge>
            )}
          </div>
        </div>
      </div>

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
                <div key={section.id} className="flex items-start gap-2 group">
                  <div className="flex flex-col gap-0.5 pt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Button variant="ghost" size="icon" className="h-5 w-5" onClick={() => handleMoveSection(index, 'up')} disabled={index === 0} aria-label="Move up">
                      <ArrowUp className="h-3 w-3" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-5 w-5" onClick={() => handleMoveSection(index, 'down')} disabled={index === sortedSections.length - 1} aria-label="Move down">
                      <ArrowDown className="h-3 w-3" />
                    </Button>
                  </div>
                  <div className="flex-1 rounded-lg border border-glass-border p-3 group-hover:border-primary/30 transition-colors">
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
    </div>
  )
}
