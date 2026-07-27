import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useResume, useResumeSections, useCreateResumeSection, useUpdateResumeSection, useDeleteResumeSection, useUpdateResume } from '@/api/hooks'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent } from '@/components/ui/card'
import { useToast } from '@/components/ui/toast'
import { ArrowLeft, Plus, Pencil, Trash2, Save, FileText } from 'lucide-react'

const sectionTypes = [
  { key: 'summary', label: 'Summary' },
  { key: 'experience', label: 'Experience' },
  { key: 'education', label: 'Education' },
  { key: 'skills', label: 'Skills' },
  { key: 'projects', label: 'Projects' },
  { key: 'certifications', label: 'Certifications' },
  { key: 'languages', label: 'Languages' },
  { key: 'custom', label: 'Custom' },
]

export function ResumeDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: resume, isLoading } = useResume(id!) as any
  const { data: sections } = useResumeSections(id!) as any
  const createSection = useCreateResumeSection(id!)
  const updateSection = useUpdateResumeSection(id!)
  const deleteSection = useDeleteResumeSection(id!)
  const updateResume = useUpdateResume()
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

  const sectionList = (sections as any) || []

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
          </div>
        </div>
      </div>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Sections</h2>
            <Button variant="outline" size="sm" onClick={() => { resetForm(); setShowForm(true) }}>
              <Plus className="h-4 w-4 mr-1" /> Add Section
            </Button>
          </div>

          {sectionList.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              No sections yet. Click "Add Section" to start building your resume.
            </p>
          ) : (
            <div className="space-y-2">
              {sectionList.map((section: any) => (
                <div key={section.id} className="flex items-center justify-between rounded-lg border border-glass-border p-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <FileText className="h-5 w-5 text-primary shrink-0" />
                    <div className="min-w-0">
                      <p className="text-sm font-medium">{section.title || section.section_type}</p>
                      {section.content?.text && (
                        <p className="text-xs text-muted-foreground truncate">{section.content.text}</p>
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
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={resetForm}>
          <div className="bg-dark-900 border border-glass-border rounded-xl p-6 w-96" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">{editingSection ? 'Edit' : 'Add'} Section</h3>
            <div className="space-y-4">
              <div>
                <label className="text-xs text-muted-foreground block mb-1">Section Type</label>
                <select className="w-full rounded-md border border-glass-border bg-dark-800 px-3 py-2 text-sm text-foreground" value={sectionType} onChange={e => setSectionType(e.target.value)}>
                  {sectionTypes.map(st => <option key={st.key} value={st.key}>{st.label}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-muted-foreground block mb-1">Title</label>
                <Input value={sectionTitle} onChange={e => setSectionTitle(e.target.value)} placeholder="e.g. Software Engineering Intern" />
              </div>
              <div>
                <label className="text-xs text-muted-foreground block mb-1">Content</label>
                <textarea className="w-full rounded-md border border-glass-border bg-dark-800 px-3 py-2 text-sm text-foreground min-h-[120px]" value={sectionContent} onChange={e => setSectionContent(e.target.value)} placeholder="Describe this section..." />
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
