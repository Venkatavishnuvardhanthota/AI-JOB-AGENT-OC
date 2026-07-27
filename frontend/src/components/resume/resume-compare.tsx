import { useCompareResumes, useResume } from '@/api/hooks'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useToast } from '@/components/ui/toast'
import { ArrowLeftRight, Plus, Minus, Edit3 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useState } from 'react'

interface ResumeCompareProps {
  resumeId: string
  versionId?: string
}

export function ResumeCompare({ resumeId, versionId }: ResumeCompareProps) {
  useResume(resumeId) as any
  const compareResumes = useCompareResumes()
  const { addToast } = useToast()
  const [rightId, setRightId] = useState(versionId || '')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const handleCompare = async () => {
    if (!rightId) return
    setLoading(true)
    try {
      const res = await compareResumes.mutateAsync({ left_id: resumeId, right_id: rightId })
      setResult(res)
    } catch {
      addToast('Failed to compare versions', 'error')
    } finally {
      setLoading(false)
    }
  }

  const getIcon = (type: string) => {
    switch (type) {
      case 'added': return <Plus className="h-4 w-4 text-success" />
      case 'removed': return <Minus className="h-4 w-4 text-error" />
      case 'modified': return <Edit3 className="h-4 w-4 text-warning" />
      default: return null
    }
  }

  const getBadge = (type: string) => {
    switch (type) {
      case 'added': return <Badge variant="success" className="text-[10px]">Added</Badge>
      case 'removed': return <Badge variant="destructive" className="text-[10px]">Removed</Badge>
      case 'modified': return <Badge variant="warning" className="text-[10px]">Modified</Badge>
      default: return null
    }
  }

  return (
    <div className="space-y-4" role="region" aria-label="Resume version comparison">
      <div className="flex items-center gap-3">
        <div className="flex-1">
          <label className="text-xs text-muted-foreground block mb-1">Resume Version to Compare Against</label>
          <input
            className="w-full rounded-md border border-glass-border bg-dark-800 px-3 py-2 text-sm text-foreground"
            value={rightId}
            onChange={e => setRightId(e.target.value)}
            placeholder="Enter resume ID or version ID..."
          />
        </div>
        <Button size="sm" className="mt-5" onClick={handleCompare} disabled={!rightId || loading}>
          <ArrowLeftRight className="h-4 w-4 mr-1" /> Compare
        </Button>
      </div>

      {loading && <Skeleton className="h-32 w-full rounded-xl" />}

      {result && !loading && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>Version {result.left_version}</span>
            <ArrowLeftRight className="h-4 w-4" />
            <span>Version {result.right_version}</span>
          </div>

          {result.changes.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">No differences found between versions.</p>
          ) : (
            <div className="space-y-2">
              {result.changes.map((change: any, i: number) => (
                <div key={i} className={cn(
                  'flex items-center gap-3 rounded-lg border p-3',
                  change.type === 'added' && 'border-success/20 bg-success/5',
                  change.type === 'removed' && 'border-error/20 bg-error/5',
                  change.type === 'modified' && 'border-warning/20 bg-warning/5',
                )}>
                  {getIcon(change.type)}
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium capitalize">{change.section}</span>
                      {getBadge(change.type)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
