import { useResumeVersions, useDuplicateResume } from '@/api/hooks'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useToast } from '@/components/ui/toast'
import { useNavigate } from 'react-router-dom'
import { Copy, Eye, ArrowLeftRight, Calendar } from 'lucide-react'
import { formatDate } from '@/lib/utils'

interface VersionHistoryProps {
  resumeId: string
  currentVersion: number
  onCompare?: (versionId: string) => void
}

export function VersionHistory({ resumeId, currentVersion, onCompare }: VersionHistoryProps) {
  const { data: versions, isLoading } = useResumeVersions(resumeId) as any
  const duplicateResume = useDuplicateResume()
  const navigate = useNavigate()
  const { addToast } = useToast()

  const handleDuplicate = async (v: any) => {
    try {
      await duplicateResume.mutateAsync({ id: v.id, data: { title: `${v.title || 'Resume'} (Copy)` } })
      addToast('Version duplicated!', 'success')
    } catch { addToast('Failed to duplicate', 'error') }
  }

  const handlePreview = (v: any) => {
    navigate(`/resumes/${v.id}`)
  }

  if (isLoading) return <Skeleton className="h-48 w-full rounded-xl" />

  const list = (versions as any) || []

  return (
    <div className="space-y-3" role="region" aria-label="Version history">
      {list.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-8">No version history available.</p>
      ) : (
        list.map((v: any) => (
          <div key={v.id} className="flex items-center justify-between rounded-lg border border-glass-border p-3 hover:bg-white/[0.03] transition-colors">
            <div className="flex items-center gap-3 min-w-0">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-bold">
                v{v.version}
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium">{v.title || `Version ${v.version}`}</p>
                  {v.version === currentVersion && <Badge variant="success" className="text-[10px]">Current</Badge>}
                  <Badge variant="outline" className="text-[10px]">{v.status}</Badge>
                  {v.source && <Badge variant="secondary" className="text-[10px]">{v.source}</Badge>}
                </div>
                {v.change_summary && <p className="text-xs text-muted-foreground mt-0.5">{v.change_summary}</p>}
                <p className="text-xs text-muted-foreground mt-0.5 flex items-center gap-1">
                  <Calendar className="h-3 w-3" /> {formatDate(v.created_at)}
                </p>
              </div>
            </div>
            <div className="flex gap-1 shrink-0">
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => handlePreview(v)} aria-label="Preview version">
                <Eye className="h-3.5 w-3.5" />
              </Button>
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => handleDuplicate(v)} aria-label="Duplicate version">
                <Copy className="h-3.5 w-3.5" />
              </Button>
              {onCompare && v.version !== currentVersion && (
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => onCompare(v.id)} aria-label="Compare with current">
                  <ArrowLeftRight className="h-3.5 w-3.5" />
                </Button>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  )
}
