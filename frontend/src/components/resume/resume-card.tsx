import { useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useToast } from '@/components/ui/toast'
import { FileText, MoreVertical, ExternalLink, Copy, Trash2, Pencil, Calendar, Layout, Sparkles, Download, TrendingUp, Heart } from 'lucide-react'
import { formatDate } from '@/lib/utils'
import { Link } from 'react-router-dom'

interface ResumeCardProps {
  resume: {
    id: string
    title: string
    version: number
    template?: string
    target_role?: string
    status: string
    section_count: number
    created_at: string
  }
  onDelete?: (id: string) => void
  onDuplicate?: (resume: any) => void
  onRename?: (id: string, title: string) => Promise<void>
  onOptimize?: (id: string) => void
  onDownload?: (id: string) => void
  atsScore?: number
  healthScore?: number
  versionCount?: number
}

export function ResumeCard({ resume, onDelete, onDuplicate, onRename, onOptimize, onDownload, atsScore, healthScore, versionCount }: ResumeCardProps) {
  const [renaming, setRenaming] = useState(false)
  const [newTitle, setNewTitle] = useState(resume.title || '')
  const [saving, setSaving] = useState(false)
  const { addToast } = useToast()

  const handleSaveRename = async () => {
    if (!newTitle.trim() || !onRename) return
    setSaving(true)
    try {
      await onRename(resume.id, newTitle.trim())
      setRenaming(false)
      addToast('Resume renamed', 'success')
    } catch {
      addToast('Failed to rename', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card className="hover:bg-white/[0.03] transition-colors group">
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <FileText className="h-5 w-5" />
            </div>
            <div className="min-w-0 flex-1">
              {renaming ? (
                <div className="flex items-center gap-1">
                  <Input
                    value={newTitle}
                    onChange={e => setNewTitle(e.target.value)}
                    className="h-7 text-sm"
                    autoFocus
                    onKeyDown={e => { if (e.key === 'Enter') handleSaveRename(); if (e.key === 'Escape') setRenaming(false) }}
                  />
                  <Button size="sm" variant="ghost" onClick={handleSaveRename} disabled={saving}>Save</Button>
                </div>
              ) : (
                <Link to={`/resumes/${resume.id}`} className="text-sm font-medium hover:text-primary truncate block">
                  {resume.title || 'Untitled Resume'}
                </Link>
              )}
              <p className="text-xs text-muted-foreground">
                v{resume.version} · {resume.section_count} sections
                {versionCount != null && ` · ${versionCount} versions`}
              </p>
            </div>
          </div>
          {!renaming && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="opacity-0 group-hover:opacity-100 transition-opacity" aria-label="Resume actions">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-44">
                <DropdownMenuItem asChild>
                  <Link to={`/resumes/${resume.id}`}>
                    <ExternalLink className="h-4 w-4 mr-2" /> Open
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => { setRenaming(true); setNewTitle(resume.title || '') }}>
                  <Pencil className="h-4 w-4 mr-2" /> Rename
                </DropdownMenuItem>
                {onDuplicate && (
                  <DropdownMenuItem onClick={() => onDuplicate(resume)}>
                    <Copy className="h-4 w-4 mr-2" /> Duplicate
                  </DropdownMenuItem>
                )}
                {onOptimize && (
                  <DropdownMenuItem onClick={() => onOptimize(resume.id)}>
                    <Sparkles className="h-4 w-4 mr-2" /> Optimize
                  </DropdownMenuItem>
                )}
                {onDownload && (
                  <DropdownMenuItem onClick={() => onDownload(resume.id)}>
                    <Download className="h-4 w-4 mr-2" /> Download
                  </DropdownMenuItem>
                )}
                <DropdownMenuSeparator />
                {onDelete && (
                  <DropdownMenuItem onClick={() => onDelete(resume.id)} className="text-error">
                    <Trash2 className="h-4 w-4 mr-2" /> Delete
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>

        <div className="flex flex-wrap gap-1.5 mb-2">
          {resume.template && (
            <Badge variant="secondary" className="text-xs gap-1">
              <Layout className="h-3 w-3" /> {resume.template}
            </Badge>
          )}
          {resume.target_role && (
            <Badge variant="outline" className="text-xs">{resume.target_role}</Badge>
          )}
          <Badge variant={resume.status === 'complete' ? 'success' : 'warning'} className="text-xs">
            {resume.status}
          </Badge>
        </div>

        {(atsScore != null || healthScore != null) && (
          <div className="flex gap-3 mb-2">
            {atsScore != null && (
              <div className="flex items-center gap-1 text-xs">
                <TrendingUp className="h-3 w-3 text-primary" />
                <span className="text-muted-foreground">ATS:</span>
                <span className={atsScore >= 70 ? 'text-success' : atsScore >= 40 ? 'text-warning' : 'text-error'}>{atsScore}%</span>
              </div>
            )}
            {healthScore != null && (
              <div className="flex items-center gap-1 text-xs">
                <Heart className="h-3 w-3 text-accent" />
                <span className="text-muted-foreground">Health:</span>
                <span className={healthScore >= 70 ? 'text-success' : healthScore >= 40 ? 'text-warning' : 'text-error'}>{healthScore}%</span>
              </div>
            )}
          </div>
        )}

        <p className="text-xs text-muted-foreground flex items-center gap-1">
          <Calendar className="h-3 w-3" /> Updated {formatDate(resume.created_at)}
        </p>
      </CardContent>
    </Card>
  )
}
