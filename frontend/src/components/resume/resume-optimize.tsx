import { useState } from 'react'
import { useOptimizeResume, useAnalyzeResume, useJobs } from '@/api/hooks'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { useToast } from '@/components/ui/toast'
import { cn } from '@/lib/utils'
import { CheckCircle2, Loader2 } from 'lucide-react'

interface ResumeOptimizeProps {
  resumeId: string
  resumeTitle: string
  onOptimized: () => void
}

type Step = 'select' | 'analyze' | 'preview' | 'done'

export function ResumeOptimize({ resumeId, resumeTitle, onOptimized }: ResumeOptimizeProps) {
  const [step, setStep] = useState<Step>('select')
  const [selectedJobId, setSelectedJobId] = useState('')
  const [targetRole, setTargetRole] = useState('')
  const [analysis, setAnalysis] = useState<any>(null)
  const optimizeResume = useOptimizeResume()
  const analyzeResume = useAnalyzeResume()
  const { data: jobs } = useJobs() as any
  const { addToast } = useToast()
  const [analyzing, setAnalyzing] = useState(false)
  const [optimizing, setOptimizing] = useState(false)

  const jobList = Array.isArray(jobs)
    ? jobs
    : (((jobs as any)?.items ?? (jobs as any)?.data?.items) || [])

  const handleAnalyze = async () => {
    if (!selectedJobId) return
    setAnalyzing(true)
    try {
      const res = await analyzeResume.mutateAsync({
        id: resumeId,
        data: { job_id: selectedJobId, target_role: targetRole || undefined },
      })
      setAnalysis(res)
      setStep('analyze')
    } catch {
      addToast('Failed to analyze', 'error')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleOptimize = async () => {
    setOptimizing(true)
    try {
      await optimizeResume.mutateAsync({
        id: resumeId,
        data: { job_id: selectedJobId, target_role: targetRole || undefined, enhance_with_ai: true },
      })
      addToast('Resume optimized! New version created.', 'success')
      setStep('done')
      onOptimized()
    } catch {
      addToast('Failed to optimize', 'error')
    } finally {
      setOptimizing(false)
    }
  }

  return (
    <div className="space-y-4" role="region" aria-label="Optimize resume">
      {step === 'select' && (
        <div className="space-y-4">
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Target Role</label>
            <input
              className="w-full rounded-md border border-glass-border bg-dark-800 px-3 py-2 text-sm text-foreground"
              value={targetRole}
              onChange={e => setTargetRole(e.target.value)}
              placeholder="e.g. Senior Software Engineer"
            />
          </div>

          <div>
            <label className="text-xs text-muted-foreground block mb-2">Select Target Job</label>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {jobList.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No saved jobs found. Search for jobs first.
                </p>
              )}
              {jobList.map((job: any) => (
                <button
                  key={job.id}
                  type="button"
                  onClick={() => setSelectedJobId(job.id)}
                  className={cn(
                    "w-full text-left rounded-lg border p-3 transition-all hover:bg-white/5",
                    selectedJobId === job.id ? "border-primary bg-primary/5" : "border-glass-border"
                  )}
                >
                  <p className="text-sm font-medium">{job.title || job.name}</p>
                  <p className="text-xs text-muted-foreground">{job.company}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="flex justify-end">
            <Button onClick={handleAnalyze} disabled={!selectedJobId || analyzing}>
              {analyzing ? <><Loader2 className="h-4 w-4 mr-1 animate-spin" /> Analyzing...</> : 'Analyze & Optimize'}
            </Button>
          </div>
        </div>
      )}

      {step === 'analyze' && analysis && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-success">
            <CheckCircle2 className="h-4 w-4" />
            <span>Analysis complete</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="border-primary/20 bg-primary/5">
              <CardContent className="p-4">
                <h4 className="text-sm font-semibold mb-2">ATS Score</h4>
                <p className="text-2xl font-bold font-mono text-primary">{analysis.ats?.overall || 0}%</p>
              </CardContent>
            </Card>
            <Card className="border-accent/20 bg-accent/5">
              <CardContent className="p-4">
                <h4 className="text-sm font-semibold mb-2">Health Score</h4>
                <p className="text-2xl font-bold font-mono text-accent">{analysis.health?.overall || 0}%</p>
              </CardContent>
            </Card>
          </div>

          {analysis.ats?.categories && (
            <div className="space-y-2">
              <h4 className="text-sm font-semibold">Breakdown</h4>
              {analysis.ats.categories.map((cat: any) => (
                <div key={cat.name} className="flex items-center gap-3 text-sm">
                  <span className="w-32 shrink-0 text-muted-foreground">{cat.name}</span>
                  <div className="flex-1 h-2 rounded-full bg-dark-700 overflow-hidden">
                    <div className={cn(
                      'h-full rounded-full',
                      cat.score >= 70 ? 'bg-success' : cat.score >= 40 ? 'bg-warning' : 'bg-error'
                    )} style={{ width: `${cat.score}%` }} />
                  </div>
                  <span className={cn(
                    'font-mono text-xs w-8 text-right',
                    cat.score >= 70 ? 'text-success' : cat.score >= 40 ? 'text-warning' : 'text-error'
                  )}>{cat.score}%</span>
                </div>
              ))}
            </div>
          )}

          {analysis.health?.recommendations && analysis.health.recommendations.length > 0 && (
            <Card>
              <CardContent className="p-4">
                <h4 className="text-sm font-semibold mb-2">Recommendations</h4>
                <ul className="space-y-1">
                  {analysis.health.recommendations.map((r: string, i: number) => (
                    <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                      <span className="text-primary mt-0.5">{i + 1}.</span>
                      {r}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setStep('select')}>Back</Button>
            <Button onClick={handleOptimize} disabled={optimizing}>
              {optimizing ? <><Loader2 className="h-4 w-4 mr-1 animate-spin" /> Optimizing...</> : 'Create Optimized Version'}
            </Button>
          </div>
        </div>
      )}

      {step === 'done' && (
        <div className="text-center py-8 space-y-3">
          <CheckCircle2 className="h-12 w-12 mx-auto text-success" />
          <h3 className="font-semibold">Optimization Complete</h3>
          <p className="text-sm text-muted-foreground">
            A new optimized version of "{resumeTitle}" has been created.
            The original resume was not modified.
          </p>
          <Button onClick={onOptimized}>View Updated Resume</Button>
        </div>
      )}
    </div>
  )
}
