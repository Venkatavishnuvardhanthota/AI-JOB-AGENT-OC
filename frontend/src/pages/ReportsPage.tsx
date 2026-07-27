import { useState } from 'react'
import { PageHeader } from '@/components/layout/page-header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/layout/empty-state'
import { BarChart3, Download, FileText, PieChart, TrendingUp } from 'lucide-react'
import { useJobStats } from '@/api/hooks'
import { useToast } from '@/components/ui/toast'

const reportTypes = [
  { id: 'applications', label: 'Applications Report', icon: FileText },
  { id: 'jobs', label: 'Jobs Overview', icon: BarChart3 },
  { id: 'matching', label: 'Match Analysis', icon: PieChart },
  { id: 'trends', label: 'Market Trends', icon: TrendingUp },
]

export function ReportsPage() {
  const { data: stats, isLoading } = useJobStats()
  const { addToast } = useToast()
  const [selectedReport, setSelectedReport] = useState('applications')

  const handleExport = () => {
    addToast('Report downloaded!', 'success')
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-32" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24 rounded-xl" />)}
        </div>
        <Skeleton className="h-64 rounded-xl" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reports"
        description="Generate and view reports."
        actions={
          <div className="flex gap-2">
            <Select value={selectedReport} onChange={e => setSelectedReport(e.target.value)}>
              {reportTypes.map(r => <option key={r.id} value={r.id}>{r.label}</option>)}
            </Select>
            <Button variant="outline" onClick={handleExport}>
              <Download className="h-4 w-4 mr-1" /> Export
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {reportTypes.map(r => (
          <Card key={r.id} className={`cursor-pointer transition-colors hover:bg-white/[0.03] ${selectedReport === r.id ? 'border-primary' : ''}`} onClick={() => setSelectedReport(r.id)}>
            <CardContent className="p-4 text-center">
              <r.icon className="h-8 w-8 mx-auto mb-2 text-primary" />
              <p className="text-sm font-medium">{r.label}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            Jobs Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          {(stats as any)?.total > 0 ? (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                {[
                  { label: 'Total Jobs', value: (stats as any)?.total || 0 },
                  { label: 'Viewed', value: (stats as any)?.viewed || 0 },
                  { label: 'Applied', value: (stats as any)?.applied || 0 },
                  { label: 'Active', value: (stats as any)?.active || 0 },
                ].map(s => (
                  <div key={s.label} className="text-center p-4 rounded-lg bg-dark-800/50">
                    <p className="text-2xl font-bold">{s.value}</p>
                    <p className="text-xs text-muted-foreground">{s.label}</p>
                  </div>
                ))}
              </div>

              {(stats as any)?.by_source && Object.keys((stats as any).by_source).length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-3">Jobs by Source</h4>
                  <div className="space-y-2">
                    {Object.entries((stats as any).by_source).map(([source, count]) => (
                      <div key={source} className="flex items-center gap-2">
                        <span className="text-sm text-muted-foreground min-w-24">{source}</span>
                        <div className="h-4 flex-1 rounded-full bg-dark-800 overflow-hidden">
                          <div className="h-full rounded-full bg-primary" style={{ width: `${((count as number) / (stats as any).total) * 100}%` }} />
                        </div>
                        <span className="text-sm text-muted-foreground min-w-12 text-right">{count as number}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <EmptyState
              icon={BarChart3}
              title="No report data yet"
              description="Start searching for jobs to see reports and analytics."
              action={<Button asChild><a href="/jobs/search">Search Jobs</a></Button>}
            />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
