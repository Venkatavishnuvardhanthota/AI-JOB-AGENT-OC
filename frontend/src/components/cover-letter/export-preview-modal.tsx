import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Download, FileText, X, Eye } from 'lucide-react'

interface ExportPreviewModalProps {
  open: boolean
  onClose: () => void
  content: string
  title: string
  onExport: (format: string) => Promise<void>
}

export function ExportPreviewModal({ open, onClose, content, title, onExport }: ExportPreviewModalProps) {
  const [exporting, setExporting] = useState<string | null>(null)

  if (!open) return null

  const handleExport = async (format: string) => {
    setExporting(format)
    try {
      await onExport(format)
      onClose()
    } catch {
      setExporting(null)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div
        className="bg-dark-800 border border-glass-border rounded-xl shadow-2xl w-[720px] max-w-[95vw] max-h-[90vh] flex flex-col"
        onClick={e => e.stopPropagation()}
        role="dialog"
        aria-label="Export preview"
      >
        <div className="flex items-center justify-between px-5 py-3 border-b border-glass-border">
          <h2 className="text-sm font-semibold flex items-center gap-2">
            <Eye className="h-4 w-4" />
            Export Preview — {title || 'Cover Letter'}
          </h2>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close preview">
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 bg-white rounded-b-lg">
          <div
            className="prose max-w-none text-sm leading-relaxed text-gray-900"
            dangerouslySetInnerHTML={{ __html: content || '<p class="text-gray-400">No content</p>' }}
          />
        </div>

        <div className="flex items-center justify-end gap-2 px-5 py-3 border-t border-glass-border">
          <Button variant="outline" size="sm" onClick={onClose}>
            <X className="h-4 w-4 mr-1" /> Close
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleExport('pdf')} disabled={exporting !== null}>
            {exporting === 'pdf' ? 'Exporting...' : <><FileText className="h-4 w-4 mr-1" /> Export PDF</>}
          </Button>
          <Button size="sm" onClick={() => handleExport('docx')} disabled={exporting !== null}>
            {exporting === 'docx' ? 'Exporting...' : <><Download className="h-4 w-4 mr-1" /> Export DOCX</>}
          </Button>
        </div>
      </div>
    </div>
  )
}
