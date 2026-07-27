import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/toast'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/components/ui/dropdown-menu'
import { analyticsService } from '@/services/analytics'
import type { Application } from '@/types'
import { Download, FileSpreadsheet, FileText } from 'lucide-react'

interface AnalyticsExportProps {
  applications: Application[]
}

export function AnalyticsExport({ applications }: AnalyticsExportProps) {
  const [exporting, setExporting] = useState(false)
  const { addToast } = useToast()

  const handleCSV = () => {
    setExporting(true)
    try {
      const csv = analyticsService.exportToCSV(applications)
      const blob = new Blob([csv], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `job-applications-${new Date().toISOString().split('T')[0]}.csv`
      a.click()
      URL.revokeObjectURL(url)
      addToast('CSV exported successfully', 'success')
    } catch {
      addToast('Failed to export CSV', 'error')
    } finally {
      setExporting(false)
    }
  }

  const handleSummary = () => {
    addToast('PDF summary export coming soon', 'info')
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" disabled={exporting}>
          <Download className="h-4 w-4 mr-1" /> Export
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-40">
        <DropdownMenuItem onSelect={handleCSV}>
          <FileSpreadsheet className="h-4 w-4 mr-2" /> CSV
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={handleSummary}>
          <FileText className="h-4 w-4 mr-2" /> PDF Summary
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
