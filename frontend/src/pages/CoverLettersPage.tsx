import { useState, useCallback } from 'react'
import { useCoverLetters, useDeleteCoverLetter, useDuplicateCoverLetter, useExportCoverLetter } from '@/api/hooks'
import { PageHeader } from '@/components/layout/page-header'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/layout/empty-state'
import { CoverLetterCard } from '@/components/cover-letter/cover-letter-card'
import { CoverLetterWizard } from '@/components/cover-letter/cover-letter-wizard'
import { useToast } from '@/components/ui/toast'
import { Sparkles, Mail } from 'lucide-react'

export function CoverLettersPage() {
  const [showWizard, setShowWizard] = useState(false)
  const { data: letters, isLoading } = useCoverLetters()
  const deleteLetter = useDeleteCoverLetter()
  const duplicateLetter = useDuplicateCoverLetter()
  const exportLetter = useExportCoverLetter()
  const { addToast } = useToast()

  const handleDelete = useCallback(async (id: string) => {
    try { await deleteLetter.mutateAsync(id); addToast('Cover letter deleted', 'info') }
    catch { addToast('Failed to delete', 'error') }
  }, [deleteLetter, addToast])

  const handleDuplicate = useCallback(async (id: string) => {
    try { await duplicateLetter.mutateAsync(id); addToast('Cover letter duplicated!', 'success') }
    catch { addToast('Failed to duplicate', 'error') }
  }, [duplicateLetter, addToast])

  const handleExport = useCallback(async (id: string, format: string) => {
    try { await exportLetter.mutateAsync({ id, format }) }
    catch { addToast('Failed to export', 'error') }
  }, [exportLetter, addToast])

  const list = (letters as any) || []
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

  if (showWizard) {
    return (
      <div className="space-y-6 max-w-3xl">
        <PageHeader
          title="Generate Cover Letter"
          description="Create a tailored cover letter for a specific job."
          actions={<Button variant="outline" onClick={() => setShowWizard(false)}>Back to All</Button>}
        />
        <CoverLetterWizard onComplete={() => setShowWizard(false)} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Cover Letters"
        description="Generate, edit, and manage your cover letters."
        actions={
          !isEmpty && (
            <Button onClick={() => setShowWizard(true)}>
              <Sparkles className="h-4 w-4 mr-1" /> New Cover Letter
            </Button>
          )
        }
      />

      {isEmpty ? (
        <EmptyState
          icon={Mail}
          title="No cover letters yet"
          description="Generate an AI-powered cover letter matched to a job and your resume."
          action={
            <div className="flex gap-3">
              <Button onClick={() => setShowWizard(true)}>
                <Sparkles className="h-4 w-4 mr-1" /> Generate Cover Letter
              </Button>
            </div>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {list.map((item: any) => (
            <CoverLetterCard
              key={item.id}
              item={item}
              onDelete={handleDelete}
              onDuplicate={handleDuplicate}
              onDownload={handleExport}
            />
          ))}
        </div>
      )}
    </div>
  )
}
