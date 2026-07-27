import { useState, useCallback } from 'react'
import { useCoverLetter, useUpdateCoverLetter, useDuplicateCoverLetter } from '@/api/hooks'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent } from '@/components/ui/card'
import { useToast } from '@/components/ui/toast'
import { cn } from '@/lib/utils'
import { History, RotateCcw, Copy, Trash2, Eye, Pencil, Check, X } from 'lucide-react'

interface VersionPanelProps {
  coverLetterId: string
  currentVersion: number
  onRestore: (content: string) => void
  onCompare: (versionA: string, versionB: string) => void
}

interface Version {
  id: string
  version: number
  title: string
  content: string
  status: string
  created_at: string
  change_summary?: string
}

export function CoverLetterVersionPanel({
  coverLetterId, currentVersion, onRestore, onCompare,
}: VersionPanelProps) {
  const { data: coverLetter } = useCoverLetter(coverLetterId) as any
  const duplicateCoverLetter = useDuplicateCoverLetter()
  const updateCoverLetter = useUpdateCoverLetter()
  const { addToast } = useToast()
  const [versions, setVersions] = useState<Version[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedVersion, setSelectedVersion] = useState<string | null>(null)
  const [renamingId, setRenamingId] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const [previewContent, setPreviewContent] = useState<string | null>(null)

  const loadVersions = useCallback(async () => {
    setLoading(true)
    try {
      const dups = await duplicateCoverLetter.mutateAsync(coverLetterId) as any
      setVersions(prev => {
        const exists = prev.some(v => v.id === dups.id)
        if (!exists) {
          return [...prev, {
            id: dups.id, version: dups.version, title: dups.title || `v${dups.version}`,
            content: dups.content || '', status: dups.status, created_at: dups.created_at,
          }]
        }
        return prev
      })
    } catch {
      addToast('Failed to load versions', 'error')
    } finally {
      setLoading(false)
    }
  }, [coverLetterId, duplicateCoverLetter, addToast])

  const handleRestore = useCallback(async (v: Version) => {
    onRestore(v.content)
    await updateCoverLetter.mutateAsync({ id: coverLetterId, data: { content: v.content } })
    addToast(`Restored version v${v.version}`, 'success')
  }, [coverLetterId, updateCoverLetter, onRestore, addToast])

  const handleRename = useCallback(async (id: string) => {
    if (!renameValue.trim()) { setRenamingId(null); return }
    await updateCoverLetter.mutateAsync({ id, data: { title: renameValue.trim() } })
    setVersions(prev => prev.map(v => v.id === id ? { ...v, title: renameValue.trim() } : v))
    setRenamingId(null)
    addToast('Version renamed', 'success')
  }, [updateCoverLetter, renameValue, addToast])

  const handleDeleteVersion = useCallback(async (id: string) => {
    try {
      await duplicateCoverLetter.mutateAsync(id)
      setVersions(prev => prev.filter(v => v.id !== id))
      addToast('Version deleted', 'info')
    } catch {
      addToast('Failed to delete version', 'error')
    }
  }, [duplicateCoverLetter, addToast])

  const handleDuplicateVersion = useCallback(async (v: Version) => {
    try {
      const result = await duplicateCoverLetter.mutateAsync(v.id) as any
      setVersions(prev => [...prev, {
        id: result.id, version: result.version, title: result.title || `v${result.version}`,
        content: result.content || '', status: result.status, created_at: result.created_at,
      }])
      addToast('Version duplicated', 'success')
    } catch {
      addToast('Failed to duplicate version', 'error')
    }
  }, [duplicateCoverLetter, addToast])

  const sortedVersions = [coverLetter, ...versions]
    .filter(Boolean)
    .sort((a: any, b: any) => (b.version || 0) - (a.version || 0))

  return (
    <div className="space-y-4" role="region" aria-label="Version history">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <History className="h-4 w-4" /> Version History
        </h3>
        <Button variant="outline" size="sm" onClick={loadVersions} disabled={loading}>
          {loading ? <Skeleton className="h-4 w-16" /> : 'Load Versions'}
        </Button>
      </div>

      {sortedVersions.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-6">No version history available</p>
      ) : (
        <div className="space-y-2 max-h-80 overflow-y-auto">
          {sortedVersions.map((v: any) => (
            <Card
              key={v.id}
              className={cn(
                'cursor-pointer transition-colors hover:bg-white/[0.03]',
                selectedVersion === v.id && 'border-accent',
              )}
              onClick={() => setSelectedVersion(selectedVersion === v.id ? null : v.id)}
            >
              <CardContent className="p-3">
                <div className="flex items-center justify-between">
                  <div className="min-w-0 flex-1">
                    {renamingId === v.id ? (
                      <div className="flex items-center gap-1">
                        <input
                          value={renameValue}
                          onChange={e => setRenameValue(e.target.value)}
                          className="text-sm bg-dark-800 border border-glass-border rounded px-1 py-0.5 w-full"
                          autoFocus
                          onKeyDown={e => { if (e.key === 'Enter') handleRename(v.id); if (e.key === 'Escape') setRenamingId(null) }}
                        />
                        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => handleRename(v.id)}><Check className="h-3 w-3" /></Button>
                        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setRenamingId(null)}><X className="h-3 w-3" /></Button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{v.title || 'Cover Letter'}</span>
                        <Badge variant="secondary" className="text-[10px]">v{v.version}</Badge>
                        {v.version === currentVersion && <Badge variant="success" className="text-[10px]">Current</Badge>}
                        <span className="text-xs text-muted-foreground">
                          {new Date(v.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {selectedVersion === v.id && (
                  <div className="flex flex-wrap gap-1 mt-2 pt-2 border-t border-glass-border">
                    {v.content && (
                      <>
                        <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={() => setPreviewContent(v.content)}>
                          <Eye className="h-3 w-3 mr-1" /> Preview
                        </Button>
                        <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={() => onCompare(coverLetter?.content || '', v.content)}>
                          <RotateCcw className="h-3 w-3 mr-1" /> Compare
                        </Button>
                      </>
                    )}
                    {v.version !== currentVersion && (
                      <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={() => handleRestore(v)}>
                        <RotateCcw className="h-3 w-3 mr-1" /> Restore
                      </Button>
                    )}
                    <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={() => handleDuplicateVersion(v)}>
                      <Copy className="h-3 w-3 mr-1" /> Duplicate
                    </Button>
                    {v.version !== currentVersion && (
                      <Button variant="ghost" size="sm" className="h-7 text-xs text-error hover:text-error" onClick={() => handleDeleteVersion(v.id)}>
                        <Trash2 className="h-3 w-3 mr-1" /> Delete
                      </Button>
                    )}
                    <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={() => { setRenamingId(v.id); setRenameValue(v.title || '') }}>
                      <Pencil className="h-3 w-3 mr-1" /> Rename
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {previewContent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setPreviewContent(null)}>
          <div className="bg-dark-800 border border-glass-border rounded-xl p-6 w-[600px] max-w-[90vw] max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold">Version Preview</h3>
              <Button variant="ghost" size="sm" onClick={() => setPreviewContent(null)}><X className="h-4 w-4" /></Button>
            </div>
            <div className="prose prose-invert max-w-none text-sm" dangerouslySetInnerHTML={{ __html: previewContent }} />
          </div>
        </div>
      )}
    </div>
  )
}
