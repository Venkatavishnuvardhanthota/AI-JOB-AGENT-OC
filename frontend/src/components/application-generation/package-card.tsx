import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { ApplicationPackage } from '@/services/application-generation/types'
import { FileText, Eye, Download, Trash2 } from 'lucide-react'

interface PackageCardProps {
  pkg: ApplicationPackage
  onView: (pkg: ApplicationPackage) => void
  onExport: (pkg: ApplicationPackage) => void
  onDelete: (id: string) => void
}

const statusVariant: Record<string, 'success' | 'warning' | 'secondary' | 'default'> = {
  ready: 'success',
  needs_review: 'warning',
  draft: 'secondary',
  exported: 'default',
  archived: 'secondary',
}

export function PackageCard({ pkg, onView, onExport, onDelete }: PackageCardProps) {
  const confidence = pkg.metadata.confidenceScore

  return (
    <Card className="p-4 space-y-3 hover:border-primary/30 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <FileText className="h-5 w-5 text-muted-foreground mt-0.5" />
          <div>
            <h3 className="text-sm font-medium">{pkg.jobTitle}</h3>
            <p className="text-xs text-muted-foreground">{pkg.companyName}</p>
          </div>
        </div>
        <Badge variant={statusVariant[pkg.status] || 'secondary'}>{pkg.status.replace('_', ' ')}</Badge>
      </div>

      <div className="flex gap-3 text-xs text-muted-foreground">
        <span>Resume: {pkg.metadata.qualityScores.resume}%</span>
        {pkg.coverLetter && <span>CL: {pkg.metadata.qualityScores.coverLetter}%</span>}
        <span>Package: {confidence}%</span>
      </div>

      <div className="w-full bg-dark-700 rounded-full h-1.5">
        <div
          className={`h-1.5 rounded-full transition-all ${confidence >= 70 ? 'bg-success' : confidence >= 50 ? 'bg-warning' : 'bg-error'}`}
          style={{ width: `${confidence}%` }}
        />
      </div>

      <div className="flex justify-end gap-1 pt-1">
        <Button variant="ghost" size="sm" onClick={() => onView(pkg)}><Eye className="h-4 w-4" /></Button>
        <Button variant="ghost" size="sm" onClick={() => onExport(pkg)}><Download className="h-4 w-4" /></Button>
        <Button variant="ghost" size="sm" onClick={() => onDelete(pkg.id)}><Trash2 className="h-4 w-4" /></Button>
      </div>
    </Card>
  )
}
