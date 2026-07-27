import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Briefcase, FileSpreadsheet, Sparkles, FileText, Cpu } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'

const WELCOME_DISMISSED_KEY = 'welcome_dialog_dismissed'

const steps = [
  {
    icon: Briefcase,
    title: 'Welcome to AI Job Agent',
    description: 'Your intelligent job search companion. Let us help you land your next role.',
    features: [
      { icon: FileSpreadsheet, label: 'Resumes', desc: 'Upload, create, and optimize professional resumes' },
      { icon: Sparkles, label: 'Cover Letters', desc: 'AI-generated cover letters tailored to each job' },
      { icon: FileText, label: 'Applications', desc: 'Track and manage your job applications' },
      { icon: Cpu, label: 'Automation', desc: 'Automated job search and application workflows' },
    ],
  },
  {
    icon: FileSpreadsheet,
    title: 'Build Your Profile',
    description: 'Start by completing your career profile — it helps match you with the right jobs.',
    action: { label: 'Complete Profile', href: '/profile' },
  },
  {
    icon: Sparkles,
    title: 'Find & Apply',
    description: 'Search jobs, get AI-powered match scores, and generate optimized applications.',
    action: { label: 'Search Jobs', href: '/jobs/search' },
  },
]

interface WelcomeDialogProps {
  onComplete: () => void
}

export function WelcomeDialog({ onComplete }: WelcomeDialogProps) {
  const navigate = useNavigate()
  const [step, setStep] = useState(0)
  const current = steps[step]
  const Icon = current.icon
  const isLast = step === steps.length - 1

  const handleSkip = useCallback(() => {
    localStorage.setItem(WELCOME_DISMISSED_KEY, 'true')
    onComplete()
  }, [onComplete])

  const handleNext = useCallback(() => {
    if (isLast) {
      localStorage.setItem(WELCOME_DISMISSED_KEY, 'true')
      onComplete()
    } else {
      setStep(s => s + 1)
    }
  }, [isLast, onComplete])

  const handleAction = useCallback(() => {
    localStorage.setItem(WELCOME_DISMISSED_KEY, 'true')
    onComplete()
    if (current.action?.href) navigate(current.action.href)
  }, [current.action, navigate, onComplete])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" role="dialog" aria-modal="true" aria-label="Welcome">
      <Card className="w-full max-w-lg animate-in fade-in zoom-in-95 duration-200">
        <CardHeader className="text-center pb-2">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/20 ring-1 ring-primary/30">
            <Icon className="h-8 w-8 text-primary" />
          </div>
          <CardTitle className="text-xl">{current.title}</CardTitle>
          <CardDescription className="text-sm">{current.description}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="mb-4">
            <Progress value={((step + 1) / steps.length) * 100} className="h-1.5" />
            <p className="text-xs text-muted-foreground text-center mt-1.5">Step {step + 1} of {steps.length}</p>
          </div>
          {'features' in current && current.features && (
            <div className="grid grid-cols-2 gap-3">
              {current.features.map((f) => {
                const Fi = f.icon
                return (
                  <div key={f.label} className="rounded-lg bg-dark-800 p-3 ring-1 ring-glass-border">
                    <Fi className="h-4 w-4 text-primary mb-1.5" />
                    <p className="text-sm font-medium">{f.label}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{f.desc}</p>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
        <CardFooter className="flex-col gap-2">
          {current.action ? (
            <>
              <Button className="w-full" onClick={handleAction}>{current.action.label}</Button>
              <Button variant="ghost" size="sm" onClick={handleSkip}>Skip for now</Button>
            </>
          ) : (
            <Button className="w-full" onClick={handleNext}>{isLast ? 'Get Started' : 'Next'}</Button>
          )}
          {!current.action && (
            <Button variant="ghost" size="sm" onClick={handleSkip}>Skip tutorial</Button>
          )}
        </CardFooter>
      </Card>
    </div>
  )
}

export function isWelcomeDismissed(): boolean {
  return localStorage.getItem(WELCOME_DISMISSED_KEY) === 'true'
}
