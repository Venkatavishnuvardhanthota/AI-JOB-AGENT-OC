import { useState } from 'react'
import { useResumes, useCreateResume, useDeleteResume, useArchiveResume, useRestoreResume, useResumeTemplates } from '@/api/hooks'
import { PageHeader } from '@/components/layout/page-header'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/layout/empty-state'
import { useToast } from '@/components/ui/toast'
import { FileSpreadsheet, Plus, Archive, Trash2, RotateCcw } from 'lucide-react'
import { formatDate } from '@/lib/utils'

export function ResumeLibraryPage() {
  const [showArchived, setShowArchived] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const { data: resumes, isLoading } = useResumes(showArchived ? true : undefined)
  const createResume = useCreateResume()
  const deleteResume = useDeleteResume()
  const archiveResume = useArchiveResume()
  const restoreResume = useRestoreResume()
  const { data: templates } = useResumeTemplates()
  const { addToast } = useToast()
  const [title, setTitle] = useState('')
  const [template, setTemplate] = useState('')

  const handleCreate = async () => {
    if (!title.trim()) return
    try {
      await createResume.mutateAsync({ title: title.trim(), template: template || undefined })
      addToast('Resume created!', 'success')
      setShowCreateModal(false)
      setTitle('')
      setTemplate('')
    } catch { addToast('Failed to create resume', 'error') }
  }

  const handleArchive = async (id: string) => {
    try { await archiveResume.mutateAsync(id); addToast('Resume archived', 'info') }
    catch { addToast('Failed to archive', 'error') }
  }

  const handleRestore = async (id: string) => {
    try { await restoreResume.mutateAsync(id); addToast('Resume restored', 'success') }
    catch { addToast('Failed to restore', 'error') }
  }

  const handleDelete = async (id: string) => {
    try { await deleteResume.mutateAsync(id); addToast('Resume deleted', 'info') }
    catch { addToast('Failed to delete', 'error') }
  }

  if (isLoading) return <div className="space-y-4">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-32 rounded-xl" />)}</div>

  return (
    <div className="space-y-6">
      <PageHeader
        title="Resume Library"
        description="Create, manage, and organize your resumes."
        actions={
          <div className="flex gap-2">
            <Button variant={showArchived ? 'default' : 'outline'} size="sm" onClick={() => setShowArchived(!showArchived)}>
              <Archive className="h-4 w-4 mr-1" /> {showArchived ? 'Active' : 'Archived'}
            </Button>
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="h-4 w-4 mr-1" /> New Resume
            </Button>
          </div>
        }
      />

      {(!(resumes as any) || (resumes as any).length === 0) ? (
        <EmptyState
          icon={FileSpreadsheet}
          title={showArchived ? 'No archived resumes' : 'No resumes yet'}
          description={showArchived ? 'Archive resumes to keep them organized.' : 'Create your first resume to get started.'}
          action={!showArchived ? <Button onClick={() => setShowCreateModal(true)}><Plus className="h-4 w-4 mr-1" /> Create Resume</Button> : undefined}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {(resumes as any).map((resume: any) => (
            <Card key={resume.id} className="hover:bg-white/[0.03] transition-colors">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-base">{resume.title}</CardTitle>
                    <p className="text-xs text-muted-foreground mt-1">
                      v{resume.version} · {resume.section_count} sections
                    </p>
                  </div>
                  <div className="flex gap-1">
                    {resume.archived ? (
                      <Button variant="ghost" size="sm" onClick={() => handleRestore(resume.id)} title="Restore">
                        <RotateCcw className="h-4 w-4" />
                      </Button>
                    ) : (
                      <>
                        <Button variant="ghost" size="sm" onClick={() => handleArchive(resume.id)} title="Archive">
                          <Archive className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDelete(resume.id)} title="Delete">
                          <Trash2 className="h-4 w-4 text-error" />
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-1 mb-2">
                  {resume.template && <Badge variant="secondary" className="text-xs">{resume.template}</Badge>}
                  <Badge variant={resume.status === 'complete' ? 'success' : 'warning'} className="text-xs">{resume.status}</Badge>
                  {resume.is_default && <Badge variant="default" className="text-xs">Default</Badge>}
                </div>
                <p className="text-xs text-muted-foreground">Created {formatDate(resume.created_at)}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowCreateModal(false)}>
          <div className="bg-dark-900 border border-glass-border rounded-xl p-6 w-96" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">Create New Resume</h3>
            <div className="space-y-4">
              <div>
                <label className="text-sm text-muted-foreground block mb-1">Title</label>
                <input className="w-full rounded-md border border-glass-border bg-dark-800 px-3 py-2 text-sm" value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Software Engineer Resume" />
              </div>
              {(templates as any) && (templates as any).length > 0 && (
                <div>
                  <label className="text-sm text-muted-foreground block mb-1">Template</label>
                  <select className="w-full rounded-md border border-glass-border bg-dark-800 px-3 py-2 text-sm" value={template} onChange={e => setTemplate(e.target.value)}>
                    <option value="">Default</option>
                    {(templates as any).map((t: any) => <option key={t.id} value={t.name}>{t.name}</option>)}
                  </select>
                </div>
              )}
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setShowCreateModal(false)}>Cancel</Button>
                <Button onClick={handleCreate} disabled={!title.trim() || createResume.isPending}>Create</Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
