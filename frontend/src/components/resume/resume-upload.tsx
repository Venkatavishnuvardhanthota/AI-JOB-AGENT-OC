import { useState, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { useToast } from '@/components/ui/toast'
import { useUploadResume } from '@/api/hooks'
import { Upload, File, AlertCircle, CheckCircle2, Loader2, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ResumeUploadProps {
  onComplete: (resumeId?: string) => void
}

const ALLOWED_TYPES = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
const MAX_SIZE = 10 * 1024 * 1024

export function ResumeUpload({ onComplete }: ResumeUploadProps) {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const { addToast } = useToast()
  const uploadResume = useUploadResume()

  const validateFile = (f: File): string | null => {
    if (!ALLOWED_TYPES.includes(f.type)) return 'Please upload a PDF or DOCX file.'
    if (f.size > MAX_SIZE) return 'File size must be under 10MB.'
    return null
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const f = e.dataTransfer.files[0]
    if (!f) return
    const err = validateFile(f)
    if (err) { setError(err); return }
    setFile(f)
    setError('')
  }

  const handleSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (!f) return
    const err = validateFile(f)
    if (err) { setError(err); return }
    setFile(f)
    setError('')
  }

  const handleUpload = async () => {
    if (!file) return
    setUploading(true)
    setProgress(0)
    setError('')

    const interval = setInterval(() => {
      setProgress(p => Math.min(p + 15, 90))
    }, 500)

    try {
      const formData = new FormData()
      formData.append('file', file)
      const result = await uploadResume.mutateAsync(formData) as any
      clearInterval(interval)
      setProgress(100)
      addToast('Resume uploaded successfully!', 'success')
      setTimeout(() => onComplete(result?.id), 1000)
    } catch (e: any) {
      clearInterval(interval)
      setError(e.message || 'Upload failed')
      addToast('Upload failed', 'error')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-4" role="region" aria-label="Resume upload">
      {!file && (
        <div
          onDrop={handleDrop}
          onDragOver={e => e.preventDefault()}
          onClick={() => inputRef.current?.click()}
          onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click() }}
          role="button"
          tabIndex={0}
          aria-label="Upload resume file"
          className={cn(
            "flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-glass-border p-8 transition-colors cursor-pointer hover:border-primary/50 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary",
            error && "border-error/50"
          )}
        >
          <Upload className="h-10 w-10 text-muted-foreground mb-3" aria-hidden="true" />
          <p className="text-sm font-medium">Drop your resume here, or click to browse</p>
          <p className="text-xs text-muted-foreground mt-1">Supports PDF, DOCX (max 10MB)</p>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx"
            className="hidden"
            onChange={handleSelect}
            aria-hidden="true"
          />
        </div>
      )}

      {file && !uploading && (
        <div className="flex items-center justify-between rounded-lg border border-glass-border p-4">
          <div className="flex items-center gap-3">
            <File className="h-8 w-8 text-primary" />
            <div>
              <p className="text-sm font-medium">{file.name}</p>
              <p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="ghost" size="icon" onClick={() => setFile(null)} aria-label="Remove file">
              <X className="h-4 w-4" />
            </Button>
            <Button size="sm" onClick={handleUpload}>
              <Upload className="h-4 w-4 mr-1" /> Upload
            </Button>
          </div>
        </div>
      )}

      {uploading && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm">
            <Loader2 className="h-4 w-4 animate-spin text-primary" />
            <span>Uploading resume...</span>
          </div>
          <Progress value={progress} aria-label="Upload progress" />
        </div>
      )}

      {!uploading && progress === 100 && (
        <div className="flex items-center gap-2 text-sm text-success">
          <CheckCircle2 className="h-4 w-4" />
          <span>Upload complete</span>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 text-sm text-error">
          <AlertCircle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}
    </div>
  )
}
