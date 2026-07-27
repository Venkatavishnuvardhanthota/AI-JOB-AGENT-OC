import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/components/ui/dropdown-menu'
import { useToast } from '@/components/ui/toast'
import type { CalendarEvent, FollowUpTask } from '@/services/calendar'
import { Download, FileSpreadsheet, FileText, Calendar } from 'lucide-react'

interface CalendarExportProps {
  events: CalendarEvent[]
  followUps: FollowUpTask[]
}

export function CalendarExport({ events, followUps }: CalendarExportProps) {
  const { addToast } = useToast()

  const exportCSV = (filename: string, headers: string[], rows: string[][]) => {
    const csv = [headers.join(','), ...rows.map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(','))].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${filename}-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
    addToast(`${filename} exported`, 'success')
  }

  const handleExportCalendar = () => {
    const headers = ['Title', 'Company', 'Date', 'Time', 'Type', 'Status', 'Notes']
    const rows = events.map(e => [
      e.title, e.subtitle, new Date(e.date).toLocaleDateString(), e.time || '', e.type, e.status, e.notes || '',
    ])
    exportCSV('career-calendar', headers, rows)
  }

  const handleExportFollowUps = () => {
    const headers = ['Title', 'Description', 'Due Date', 'Type', 'Status']
    const rows = followUps.map(f => [
      f.title, f.description, new Date(f.dueDate).toLocaleDateString(), f.type, f.status,
    ])
    exportCSV('follow-up-planner', headers, rows)
  }

  const handleExportAgenda = () => {
    const sorted = [...events].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    const headers = ['Date', 'Title', 'Company', 'Time', 'Type', 'Status']
    const rows = sorted.map(e => [
      new Date(e.date).toLocaleDateString(), e.title, e.subtitle, e.time || '', e.type, e.status,
    ])
    exportCSV('career-agenda', headers, rows)
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm">
          <Download className="h-4 w-4 mr-1" /> Export
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-44">
        <DropdownMenuItem onSelect={handleExportCalendar}>
          <Calendar className="h-4 w-4 mr-2" /> Calendar CSV
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={handleExportAgenda}>
          <FileText className="h-4 w-4 mr-2" /> Agenda CSV
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={handleExportFollowUps}>
          <FileSpreadsheet className="h-4 w-4 mr-2" /> Follow-up Plan CSV
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
