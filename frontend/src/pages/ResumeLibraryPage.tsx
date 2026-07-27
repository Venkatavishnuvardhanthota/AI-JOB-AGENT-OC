import { useState } from 'react'
import { useResumes, useDeleteResume, useUpdateResume } from '@/api/hooks'
import { PageHeader } from '@/components/layout/page-header'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/layout/empty-state'
import { CreateResumeModal } from '@/components/resume/create-resume-modal'
import { ResumeCard } from '@/components/resume/resume-card'
import { useToast } from '@/components/ui/toast'
import { FileSpreadsheet, Upload, Sparkles } from 'lucide-react'

export function ResumeLibraryPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const { data: resumes, isLoading } = useResumes()
  const deleteResume = useDeleteResume()
  const updateResume = useUpdateResume()
  const { addToast } = useToast()

  const handleDelete = async (id: string) => {
    try { await deleteResume.mutateAsync(id); addToast('Resume deleted', 'info') }
    catch { addToast('Failed to delete', 'error') }
  }

  const handleDuplicate = () => {
    setShowCreateModal(true)
  }

  const handleRename = async (id: string, title: string) => {
    await updateResume.mutateAsync({ id, data: { title } })
  }

  const list = (resumes as any) || []
  const isEmpty = !isLoading && list.length === 0

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-40 rounded-xl" />)}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Resume Library"
        description="Create, manage, and organize your resumes."
        actions={
          !isEmpty && (
            <Button onClick={() => setShowCreateModal(true)}>
              <Upload className="h-4 w-4 mr-1" /> New Resume
            </Button>
          )
        }
      />

      {isEmpty ? (
        <EmptyState
          icon={FileSpreadsheet}
          title="No resumes yet"
          description="Upload an existing resume or create one from your profile."
          action={
            <div className="flex gap-3">
              <Button onClick={() => setShowCreateModal(true)}>
                <Upload className="h-4 w-4 mr-1" /> Upload Resume
              </Button>
              <Button variant="outline" onClick={() => setShowCreateModal(true)}>
                <Sparkles className="h-4 w-4 mr-1" /> Generate Resume
              </Button>
            </div>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {list.map((resume: any) => (
            <ResumeCard
              key={resume.id}
              resume={resume}
              onDelete={handleDelete}
              onDuplicate={handleDuplicate}
              onRename={handleRename}
            />
          ))}
        </div>
      )}

      <CreateResumeModal
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreated={() => {
          setShowCreateModal(false)
          addToast('Resume created!', 'success')
        }}
        resumes={list}
      />
    </div>
  )
}
