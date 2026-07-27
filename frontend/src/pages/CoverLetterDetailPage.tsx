import { useCallback } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import {
  useCoverLetter, useDeleteCoverLetter, useDuplicateCoverLetter,
  useExportCoverLetter,
} from '@/api/hooks'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useToast } from '@/components/ui/toast'
import { CoverLetterEditor } from '@/components/cover-letter/cover-letter-editor'
import { ApplicationPackageReview } from '@/components/cover-letter/application-package-review'
import { CoverLetterCompare } from '@/components/cover-letter/cover-letter-compare'
import { CompanyIntel } from '@/components/cover-letter/company-intel'
import {
  ArrowLeft, Edit, Package, Download, Copy, Trash2,
  ArrowLeftRight, Building2,
} from 'lucide-react'

export function CoverLetterDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: coverLetter, isLoading } = useCoverLetter(id!) as any
  const deleteCoverLetter = useDeleteCoverLetter()
  const duplicateCoverLetter = useDuplicateCoverLetter()
  const exportCoverLetter = useExportCoverLetter()
  const { addToast } = useToast()

  const handleDelete = useCallback(async () => {
    try {
      await deleteCoverLetter.mutateAsync(id!)
      addToast('Cover letter deleted', 'info')
      navigate('/cover-letters')
    } catch {
      addToast('Failed to delete', 'error')
    }
  }, [id, deleteCoverLetter, navigate, addToast])

  const handleDuplicate = useCallback(async () => {
    try {
      const result = await duplicateCoverLetter.mutateAsync(id!) as any
      addToast('Cover letter duplicated!', 'success')
      if (result?.id) navigate(`/cover-letters/${result.id}`)
    } catch {
      addToast('Failed to duplicate', 'error')
    }
  }, [id, duplicateCoverLetter, navigate, addToast])

  const handleExport = useCallback(async (format: string) => {
    try { await exportCoverLetter.mutateAsync({ id: id!, format }) }
    catch { addToast('Failed to export', 'error') }
  }, [id, exportCoverLetter, addToast])

  if (isLoading) return (
    <div className="space-y-6 max-w-5xl">
      <Skeleton className="h-8 w-48" />
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-3"><Skeleton className="h-64 rounded-xl" /></div>
        <div><Skeleton className="h-40 rounded-xl" /></div>
      </div>
    </div>
  )

  if (!coverLetter) return (
    <div className="text-center py-16 text-muted-foreground">
      <p className="text-lg mb-2">Cover letter not found</p>
      <Button variant="outline" asChild><Link to="/cover-letters">Back to Cover Letters</Link></Button>
    </div>
  )

  return (
    <div className="space-y-6 max-w-5xl">
      <Link to="/cover-letters" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-2">
        <ArrowLeft className="h-4 w-4" /> Back to Cover Letters
      </Link>

      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div className="space-y-1 flex-1 min-w-0">
          <h1 className="text-2xl font-bold text-foreground truncate">
            {coverLetter.title || 'Cover Letter'}
          </h1>
          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <span>v{coverLetter.version}</span>
            <Badge variant={coverLetter.status === 'ready' ? 'success' : 'warning'} className="text-xs">{coverLetter.status}</Badge>
            {coverLetter.tone && <Badge variant="secondary" className="text-xs">{coverLetter.tone}</Badge>}
            {coverLetter.company_name && <span>{coverLetter.company_name}</span>}
            {coverLetter.job_title && <span>— {coverLetter.job_title}</span>}
          </div>
        </div>
        <div className="flex flex-wrap gap-2 shrink-0">
          <Button variant="outline" size="sm" onClick={handleDuplicate}>
            <Copy className="h-4 w-4 mr-1" /> Duplicate
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleExport('pdf')}>
            <Download className="h-4 w-4 mr-1" /> PDF
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleExport('docx')}>
            <Download className="h-4 w-4 mr-1" /> DOCX
          </Button>
          <Button variant="outline" size="sm" onClick={handleDelete} className="text-error">
            <Trash2 className="h-4 w-4 mr-1" /> Delete
          </Button>
        </div>
      </div>

      <Tabs defaultValue={coverLetter.job_id ? 'editor' : 'editor'}>
        <TabsList className="flex-wrap">
          <TabsTrigger value="editor" aria-controls="tab-editor">
            <Edit className="h-4 w-4 mr-1" /> Editor
          </TabsTrigger>
          <TabsTrigger value="package" aria-controls="tab-package">
            <Package className="h-4 w-4 mr-1" /> Application Package
          </TabsTrigger>
          <TabsTrigger value="compare" aria-controls="tab-compare">
            <ArrowLeftRight className="h-4 w-4 mr-1" /> Compare
          </TabsTrigger>
          <TabsTrigger value="company" aria-controls="tab-company">
            <Building2 className="h-4 w-4 mr-1" /> Company
          </TabsTrigger>
        </TabsList>

        <TabsContent value="editor" className="mt-6" id="tab-editor">
          <CoverLetterEditor
            coverLetter={coverLetter}
            onSaved={() => {}}
          />
        </TabsContent>

        <TabsContent value="package" className="mt-6" id="tab-package">
          {coverLetter.resume_id && coverLetter.job_id ? (
            <ApplicationPackageReview
              jobId={coverLetter.job_id}
              resumeId={coverLetter.resume_id}
              coverLetterId={coverLetter.id}
              onDownload={handleExport}
            />
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <Package className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>Link this cover letter to a job and resume to create an application package.</p>
            </div>
          )}
        </TabsContent>

        <TabsContent value="compare" className="mt-6" id="tab-compare">
          <CoverLetterCompare
            original={coverLetter.content || ''}
            edited={coverLetter.content || ''}
            labelA="Saved"
            labelB="Edited"
          />
        </TabsContent>

        <TabsContent value="company" className="mt-6" id="tab-company">
          <CompanyIntel jobId={coverLetter.job_id} companyName={coverLetter.company_name} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
