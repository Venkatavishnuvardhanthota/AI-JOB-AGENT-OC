import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { FileText, MoreVertical, ExternalLink, Copy, Download, Trash2, Calendar } from 'lucide-react'
import { formatDate } from '@/lib/utils'
import { Link } from 'react-router-dom'

interface CoverLetterCardProps {
  item: {
    id: string
    title?: string
    company_name?: string
    job_title?: string
    template?: string
    version: number
    status: string
    created_at: string
    updated_at: string
  }
  onDelete?: (id: string) => void
  onDuplicate?: (id: string) => void
  onDownload?: (id: string, format: string) => void
}

export function CoverLetterCard({ item, onDelete, onDuplicate, onDownload }: CoverLetterCardProps) {
  return (
    <Card className="hover:bg-white/[0.03] transition-colors group">
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent/10 text-accent">
              <FileText className="h-5 w-5" />
            </div>
            <div className="min-w-0 flex-1">
              <Link to={`/cover-letters/${item.id}`} className="text-sm font-medium hover:text-accent truncate block">
                {item.title || 'Cover Letter'}
              </Link>
              <p className="text-xs text-muted-foreground">
                {item.company_name && `${item.company_name}`}
                {item.job_title && ` — ${item.job_title}`}
                {!item.company_name && !item.job_title && `v${item.version}`}
              </p>
            </div>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="opacity-0 group-hover:opacity-100 transition-opacity" aria-label="Actions">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-44">
              <DropdownMenuItem asChild>
                <Link to={`/cover-letters/${item.id}`}>
                  <ExternalLink className="h-4 w-4 mr-2" /> Open
                </Link>
              </DropdownMenuItem>
              {onDuplicate && (
                <DropdownMenuItem onClick={() => onDuplicate(item.id)}>
                  <Copy className="h-4 w-4 mr-2" /> Duplicate
                </DropdownMenuItem>
              )}
              {onDownload && (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => onDownload(item.id, 'pdf')}>
                    <Download className="h-4 w-4 mr-2" /> Download PDF
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onDownload(item.id, 'docx')}>
                    <Download className="h-4 w-4 mr-2" /> Download DOCX
                  </DropdownMenuItem>
                </>
              )}
              <DropdownMenuSeparator />
              {onDelete && (
                <DropdownMenuItem onClick={() => onDelete(item.id)} className="text-error">
                  <Trash2 className="h-4 w-4 mr-2" /> Delete
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <div className="flex flex-wrap gap-1.5 mb-2">
          {item.status && (
            <Badge variant={item.status === 'ready' ? 'success' : 'warning'} className="text-xs">
              {item.status}
            </Badge>
          )}
          {item.template && <Badge variant="secondary" className="text-xs">{item.template}</Badge>}
        </div>

        <p className="text-xs text-muted-foreground flex items-center gap-1">
          <Calendar className="h-3 w-3" /> Updated {formatDate(item.updated_at || item.created_at)}
        </p>
      </CardContent>
    </Card>
  )
}
