import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { EmptyState } from '@/components/layout/empty-state'
import { FileText, FileSpreadsheet, Download, Eye } from 'lucide-react'
import { Link } from 'react-router-dom'

export interface DocumentRef {
  id: string
  type: 'resume' | 'cover_letter'
  name: string
  version?: string
  created_at: string
  file_url?: string
}

interface ApplicationDocumentsProps {
  resume?: DocumentRef | null
  coverLetter?: DocumentRef | null
}

export function ApplicationDocuments({ resume, coverLetter }: ApplicationDocumentsProps) {
  const hasDocs = resume || coverLetter

  if (!hasDocs) {
    return (
      <Card>
        <CardHeader><CardTitle>Documents</CardTitle></CardHeader>
        <CardContent>
          <EmptyState icon={FileText} title="No documents" description="Attach a resume and cover letter to this application." />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader><CardTitle>Documents</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {resume && (
          <div className="flex items-center gap-3 p-3 rounded-lg bg-dark-800/30 border border-glass-border">
            <FileSpreadsheet className="h-8 w-8 text-primary shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <p className="text-sm font-medium truncate">{resume.name}</p>
                <Badge variant="secondary" className="text-[10px]">Resume</Badge>
              </div>
              {resume.version && <p className="text-xs text-muted-foreground">v{resume.version}</p>}
            </div>
            <div className="flex gap-1 shrink-0">
              <Link to={`/resumes/${resume.id}`}>
                <Button variant="ghost" size="icon" className="h-8 w-8" aria-label="Preview resume">
                  <Eye className="h-4 w-4" />
                </Button>
              </Link>
              {resume.file_url && (
                <Button variant="ghost" size="icon" className="h-8 w-8" asChild aria-label="Download resume">
                  <a href={resume.file_url} download>
                    <Download className="h-4 w-4" />
                  </a>
                </Button>
              )}
            </div>
          </div>
        )}
        {coverLetter && (
          <div className="flex items-center gap-3 p-3 rounded-lg bg-dark-800/30 border border-glass-border">
            <FileText className="h-8 w-8 text-secondary shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <p className="text-sm font-medium truncate">{coverLetter.name}</p>
                <Badge variant="secondary" className="text-[10px]">Cover Letter</Badge>
              </div>
              {coverLetter.version && <p className="text-xs text-muted-foreground">v{coverLetter.version}</p>}
            </div>
            <div className="flex gap-1 shrink-0">
              <Link to={`/cover-letters/${coverLetter.id}`}>
                <Button variant="ghost" size="icon" className="h-8 w-8" aria-label="Preview cover letter">
                  <Eye className="h-4 w-4" />
                </Button>
              </Link>
              {coverLetter.file_url && (
                <Button variant="ghost" size="icon" className="h-8 w-8" asChild aria-label="Download cover letter">
                  <a href={coverLetter.file_url} download>
                    <Download className="h-4 w-4" />
                  </a>
                </Button>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
