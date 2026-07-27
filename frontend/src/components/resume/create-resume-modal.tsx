import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Upload, Sparkles, FileText, Copy, ArrowLeft } from 'lucide-react'
import { ResumeUpload } from './resume-upload'
import { ResumeWizard } from './resume-wizard'

interface CreateResumeModalProps {
  open: boolean
  onClose: () => void
  onCreated: () => void
  resumes?: any[]
}

type Step = 'choose' | 'upload' | 'generate' | 'blank' | 'duplicate'

export function CreateResumeModal({ open, onClose, onCreated, resumes = [] }: CreateResumeModalProps) {
  const [step, setStep] = useState<Step>('choose')

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Create resume"
    >
      <div
        className="bg-dark-900 border border-glass-border rounded-xl w-full max-w-2xl max-h-[85vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        {step === 'choose' && (
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-1">Create Resume</h2>
            <p className="text-sm text-muted-foreground mb-6">Choose how you'd like to start.</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => setStep('upload')}
                className="relative flex flex-col items-start gap-3 rounded-xl border-2 border-primary/30 bg-primary/5 p-5 text-left transition-all hover:border-primary hover:bg-primary/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                aria-label="Upload existing resume"
              >
                <span className="absolute top-2 right-2 text-[10px] font-semibold text-primary bg-primary/10 px-2 py-0.5 rounded-full">Recommended</span>
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/20 text-primary">
                  <Upload className="h-6 w-6" />
                </div>
                <div>
                  <p className="font-semibold">Upload Existing Resume</p>
                  <p className="text-xs text-muted-foreground mt-1">Upload a PDF or DOCX and we'll automatically extract your information.</p>
                </div>
              </button>

              <button
                type="button"
                onClick={() => setStep('generate')}
                className="flex flex-col items-start gap-3 rounded-xl border border-glass-border p-5 text-left transition-all hover:bg-white/5 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                aria-label="Generate from career profile"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-accent/20 text-accent">
                  <Sparkles className="h-6 w-6" />
                </div>
                <div>
                  <p className="font-semibold">Generate From Career Profile</p>
                  <p className="text-xs text-muted-foreground mt-1">Use your saved profile to generate a professional ATS resume.</p>
                </div>
              </button>

              <button
                type="button"
                onClick={() => setStep('blank')}
                className="flex flex-col items-start gap-3 rounded-xl border border-glass-border p-5 text-left transition-all hover:bg-white/5 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                aria-label="Create blank resume"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-dark-600 text-foreground">
                  <FileText className="h-6 w-6" />
                </div>
                <div>
                  <p className="font-semibold">Create Blank Resume</p>
                  <p className="text-xs text-muted-foreground mt-1">Build a resume manually from scratch.</p>
                </div>
              </button>

              {resumes.length > 0 && (
                <button
                  type="button"
                  onClick={() => setStep('duplicate')}
                  className="flex flex-col items-start gap-3 rounded-xl border border-glass-border p-5 text-left transition-all hover:bg-white/5 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  aria-label="Duplicate existing resume"
                >
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-warning/20 text-warning">
                    <Copy className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="font-semibold">Duplicate Existing Resume</p>
                    <p className="text-xs text-muted-foreground mt-1">Create another version from an existing resume.</p>
                  </div>
                </button>
              )}
            </div>

            <div className="flex justify-end mt-6">
              <Button variant="ghost" onClick={onClose}>Cancel</Button>
            </div>
          </div>
        )}

        {step === 'upload' && (
          <div className="p-6">
            <button
              type="button"
              onClick={() => setStep('choose')}
              className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4"
            >
              <ArrowLeft className="h-4 w-4" /> Back
            </button>
            <h2 className="text-xl font-semibold mb-4">Upload Resume</h2>
            <ResumeUpload onComplete={() => { onCreated(); onClose() }} />
          </div>
        )}

        {step === 'generate' && (
          <div className="p-6">
            <button
              type="button"
              onClick={() => setStep('choose')}
              className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4"
            >
              <ArrowLeft className="h-4 w-4" /> Back
            </button>
            <h2 className="text-xl font-semibold mb-4">Generate From Career Profile</h2>
            <p className="text-sm text-muted-foreground mb-4">Select sections to include in your generated resume.</p>
            <ResumeWizard mode="generate" onComplete={() => { onCreated(); onClose() }} />
          </div>
        )}

        {step === 'blank' && (
          <div className="p-6">
            <button
              type="button"
              onClick={() => setStep('choose')}
              className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4"
            >
              <ArrowLeft className="h-4 w-4" /> Back
            </button>
            <h2 className="text-xl font-semibold mb-4">Create Blank Resume</h2>
            <ResumeWizard mode="blank" onComplete={() => { onCreated(); onClose() }} />
          </div>
        )}

        {step === 'duplicate' && (
          <div className="p-6">
            <button
              type="button"
              onClick={() => setStep('choose')}
              className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4"
            >
              <ArrowLeft className="h-4 w-4" /> Back
            </button>
            <h2 className="text-xl font-semibold mb-4">Duplicate Resume</h2>
            <ResumeWizard mode="duplicate" resumes={resumes} onComplete={() => { onCreated(); onClose() }} />
          </div>
        )}
      </div>
    </div>
  )
}
