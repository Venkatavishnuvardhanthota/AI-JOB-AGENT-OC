import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useResumes, useDeleteResume, useUpdateResume, useDownloadResume } from '@/api/hooks'
import { PageHeader } from '@/components/layout/page-header'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { EmptyState } from '@/components/layout/empty-state'
import { CreateResumeModal } from '@/components/resume/create-resume-modal'
import { ResumeCard } from '@/components/resume/resume-card'
import { useToast } from '@/components/ui/toast'
import { FileSpreadsheet, Upload, Sparkles, Wand2 } from 'lucide-react'

type LibraryTab = 'master' | 'generated'

export function ResumeLibraryPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [activeTab, setActiveTab] = useState<LibraryTab>('master')
  const { data: resumes, isLoading } = useResumes(undefined, activeTab)
  const deleteResume = useDeleteResume()
  const updateResume = useUpdateResume()
  const downloadResume = useDownloadResume()
  const { addToast } = useToast()
  const navigate = useNavigate()

  const handleDelete = useCallback(async (id: string) => {
    try { await deleteResume.mutateAsync(id); addToast('Resume deleted', 'info') }
    catch { addToast('Failed to delete', 'error') }
  }, [deleteResume, addToast])

  const handleDuplicate = useCallback(() => {
    setShowCreateModal(true)
  }, [])

  const handleRename = useCallback(async (id: string, title: string) => {
    await updateResume.mutateAsync({ id, data: { title } })
  }, [updateResume])

  const handleOptimize = useCallback((id: string) => {
    navigate(`/resumes/${id}?tab=optimize`)
  }, [navigate])

  const handleDownload = useCallback(async (id: string) => {
    try { await downloadResume.mutateAsync({ id, format: 'pdf' }) }
    catch { addToast('Failed to download', 'error') }
  }, [downloadResume, addToast])

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

  const renderList = (items: any[], emptyTitle: string, emptyDescription: string, icon: any) =>
    items.length === 0 ? (
      <EmptyState
        icon={icon}
        title={emptyTitle}
        description={emptyDescription}
        action={
          activeTab === 'master' ? (
            <div className="flex gap-3">
              <Button onClick={() => setShowCreateModal(true)}>
                <Upload className="h-4 w-4 mr-1" /> Upload Resume
              </Button>
              <Button variant="outline" onClick={() => setShowCreateModal(true)}>
                <Sparkles className="h-4 w-4 mr-1" /> Generate Resume
              </Button>
            </div>
          ) : undefined
        }
      />
    ) : (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map((resume: any) => (
          <ResumeCard
            key={resume.id}
            resume={resume}
            onDelete={handleDelete}
            onDuplicate={handleDuplicate}
            onRename={handleRename}
            onOptimize={handleOptimize}
            onDownload={handleDownload}
          />
        ))}
      </div>
    )

  return (
    <div className="space-y-6">
      <PageHeader
        title="Resume Library"
        description="Create, manage, and organize your resumes."
        actions={
          activeTab === 'master' && !isEmpty && (
            <Button onClick={() => setShowCreateModal(true)}>
              <Upload className="h-4 w-4 mr-1" /> New Resume
            </Button>
          )
        }
      />

      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as LibraryTab)}>
        <TabsList>
          <TabsTrigger value="master">
            <FileSpreadsheet className="h-4 w-4 mr-1.5" />
            My Resumes
          </TabsTrigger>
          <TabsTrigger value="generated">
            <Wand2 className="h-4 w-4 mr-1.5" />
            AI Generated
          </TabsTrigger>
        </TabsList>

        <TabsContent value="master" className="mt-4">
          {renderList(
            list,
            'No resumes yet',
            'Upload an existing resume or create one from your profile.',
            FileSpreadsheet,
          )}
        </TabsContent>

        <TabsContent value="generated" className="mt-4">
          {renderList(
            list,
            'No AI-generated resumes yet',
            'When you tailor or generate a resume for a job, it appears here for reuse.',
            Wand2,
          )}
        </TabsContent>
      </Tabs>

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
