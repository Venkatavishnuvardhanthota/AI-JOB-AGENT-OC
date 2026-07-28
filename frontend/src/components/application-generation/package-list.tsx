import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { PackageCard } from './package-card'
import { applicationGenerationService } from '@/services/application-generation/application-generation'
import { exportPackage as runExport } from '@/services/application-generation/export-engine'
import type { ApplicationPackage } from '@/services/application-generation/types'
import { FileText, Download, ArrowLeft, ChevronLeft, ChevronRight } from 'lucide-react'

export function PackageList() {
  const [packages, setPackages] = useState<ApplicationPackage[]>([])
  const [selected, setSelected] = useState<ApplicationPackage | null>(null)
  const [page, setPage] = useState(0)
  const perPage = 10

  const refresh = () => setPackages(applicationGenerationService.getAllPackages())
  useEffect(() => { refresh() }, [])

  const paginated = packages.slice(page * perPage, (page + 1) * perPage)
  const totalPages = Math.ceil(packages.length / perPage)

  const handleExport = (pkg: ApplicationPackage) => {
    runExport(pkg, 'pdf')
  }

  const handleDelete = (id: string) => {
    applicationGenerationService.deletePackage(id)
    if (selected?.id === id) setSelected(null)
    refresh()
  }

  if (selected) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" size="sm" onClick={() => setSelected(null)}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Back to Packages
        </Button>
        <PackageDetail pkg={selected} />
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium">Generated Packages ({packages.length})</h3>
      {packages.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No application packages generated yet.</p>
          <p className="text-xs">Use the generator to create a tailored application package.</p>
        </div>
      )}
      <div className="space-y-3">
        {paginated.map(pkg => (
          <PackageCard key={pkg.id} pkg={pkg} onView={setSelected} onExport={handleExport} onDelete={handleDelete} />
        ))}
      </div>
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 pt-2">
          <Button variant="ghost" size="sm" disabled={page === 0} onClick={() => setPage(p => p - 1)}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-xs text-muted-foreground">Page {page + 1} of {totalPages}</span>
          <Button variant="ghost" size="sm" disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)}>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  )
}

function PackageDetail({ pkg }: { pkg: ApplicationPackage }) {
  return (
    <div className="space-y-4">
      <Card className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">{pkg.jobTitle}</h2>
            <p className="text-sm text-muted-foreground">{pkg.companyName}</p>
          </div>
          <Badge variant={pkg.status === 'ready' ? 'success' : 'warning'}>{pkg.status.replace('_', ' ')}</Badge>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-sm">
          <div><span className="text-muted-foreground">Resume Score:</span> <span className="font-medium">{pkg.metadata.qualityScores.resume}%</span></div>
          {pkg.coverLetter && <div><span className="text-muted-foreground">Cover Letter:</span> <span className="font-medium">{pkg.metadata.qualityScores.coverLetter}%</span></div>}
          <div><span className="text-muted-foreground">ATS Readiness:</span> <span className="font-medium">{pkg.metadata.qualityScores.atsReadiness}%</span></div>
          <div><span className="text-muted-foreground">Confidence:</span> <span className="font-medium">{pkg.metadata.confidenceScore}%</span></div>
        </div>

        <div className="w-full bg-dark-700 rounded-full h-2">
          <div
            className={`h-2 rounded-full ${pkg.metadata.confidenceScore >= 70 ? 'bg-success' : pkg.metadata.confidenceScore >= 50 ? 'bg-warning' : 'bg-error'}`}
            style={{ width: `${pkg.metadata.confidenceScore}%` }}
          />
        </div>
      </Card>

      <Card className="p-4 space-y-2">
        <h3 className="text-sm font-medium">Resume Summary</h3>
        <p className="text-sm text-muted-foreground">{pkg.resume.summary}</p>
        <div className="flex flex-wrap gap-1 pt-1">
          {pkg.resume.skills.filter(s => s.highlighted).map(s => (
            <Badge key={s.name} variant="secondary" className="text-xs">{s.name}</Badge>
          ))}
        </div>
      </Card>

      {pkg.coverLetter && (
        <Card className="p-4 space-y-2">
          <h3 className="text-sm font-medium">Cover Letter</h3>
          <p className="text-sm text-muted-foreground whitespace-pre-line">{pkg.coverLetter.body}</p>
        </Card>
      )}

      {pkg.metadata.reviewResults.length > 0 && (
        <Card className="p-4 space-y-2">
          <h3 className="text-sm font-medium">Review Results</h3>
          {pkg.metadata.reviewResults.map(r => (
            <div key={r.id} className="flex items-start gap-2 text-sm">
              <Badge variant={r.severity === 'error' ? 'destructive' : r.severity === 'warning' ? 'warning' : 'secondary'} className="shrink-0">
                {r.severity}
              </Badge>
              <div>
                <p className="text-sm">{r.message}</p>
                {r.suggestion && <p className="text-xs text-muted-foreground mt-0.5">{r.suggestion}</p>}
              </div>
            </div>
          ))}
        </Card>
      )}

      <div className="flex gap-2">
        <Button size="sm" onClick={() => runExport(pkg, 'pdf')}>
          <Download className="h-4 w-4 mr-1" /> Export PDF
        </Button>
        <Button size="sm" variant="secondary" onClick={() => runExport(pkg, 'docx')}>
          <Download className="h-4 w-4 mr-1" /> Export DOCX
        </Button>
        <Button size="sm" variant="secondary" onClick={() => runExport(pkg, 'markdown')}>
          <Download className="h-4 w-4 mr-1" /> Export MD
        </Button>
      </div>
    </div>
  )
}
