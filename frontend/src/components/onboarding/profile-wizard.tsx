import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useToast } from '@/components/ui/toast'
import { useUpdateProfile, useUploadResume } from '@/api/hooks'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { User, Target, Wrench, Briefcase, GraduationCap, Upload, CheckCircle, Sparkles } from 'lucide-react'

interface WizardStep {
  id: string
  icon: typeof User
  title: string
  description: string
  skippable: boolean
}

const steps: WizardStep[] = [
  { id: 'basic', icon: User, title: 'Basic Information', description: 'Tell us about yourself', skippable: false },
  { id: 'goals', icon: Target, title: 'Career Goals', description: 'What are you looking for?', skippable: true },
  { id: 'skills', icon: Wrench, title: 'Skills', description: 'Add your key skills', skippable: true },
  { id: 'experience', icon: Briefcase, title: 'Experience', description: 'Your work history', skippable: true },
  { id: 'education', icon: GraduationCap, title: 'Education', description: 'Your academic background', skippable: true },
  { id: 'resume', icon: Upload, title: 'Resume Upload', description: 'Upload or create a resume', skippable: true },
  { id: 'profile', icon: CheckCircle, title: 'Career Profile', description: 'Complete your profile', skippable: false },
  { id: 'finish', icon: Sparkles, title: 'All Set!', description: 'You\'re ready to search and apply', skippable: false },
]

const basicSchema = z.object({
  headline: z.string().max(200).optional(),
  location: z.string().max(100).optional(),
  phone: z.string().max(20).optional(),
})

type BasicForm = z.infer<typeof basicSchema>

interface ProfileWizardProps {
  onComplete: () => void
}

export function ProfileWizard({ onComplete }: ProfileWizardProps) {
  const navigate = useNavigate()
  const { addToast } = useToast()
  const updateProfile = useUpdateProfile()
  const uploadResume = useUploadResume()
  const [step, setStep] = useState(0)
  const [uploading, setUploading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const current = steps[step]
  const Icon = current.icon
  const isLast = step === steps.length - 1
  const progress = ((step + 1) / steps.length) * 100

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<BasicForm>({
    resolver: zodResolver(basicSchema),
    defaultValues: { headline: '', location: '', phone: '' },
  })

  const handleNext = useCallback(() => {
    if (isLast) {
      localStorage.setItem('profile_wizard_completed', 'true')
      onComplete()
      navigate('/dashboard')
    } else if (current.skippable) {
      setStep(s => s + 1)
    }
  }, [isLast, current.skippable, onComplete, navigate])

  const handleSkip = useCallback(() => {
    if (isLast) {
      handleNext()
    } else {
      setStep(s => s + 1)
    }
  }, [isLast, handleNext])

  const handleBasicSubmit = useCallback(async (data: BasicForm) => {
    setSubmitting(true)
    try {
      await updateProfile.mutateAsync({
        headline: data.headline || '',
        location: data.location || '',
        phone: data.phone || '',
      })
      setStep(s => s + 1)
    } catch {
      addToast('Failed to save basic information.', 'error')
    } finally {
      setSubmitting(false)
    }
  }, [updateProfile, addToast])

  const handleResumeUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      await uploadResume.mutateAsync(formData)
      addToast('Resume uploaded successfully!', 'success')
      setStep(s => s + 1)
    } catch {
      addToast('Failed to upload resume.', 'error')
    } finally {
      setUploading(false)
    }
  }, [uploadResume, addToast])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 overflow-y-auto" role="dialog" aria-modal="true" aria-label="Profile setup wizard">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center pb-2">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/20 ring-1 ring-primary/30">
            <Icon className="h-7 w-7 text-primary" />
          </div>
          <CardTitle className="text-lg">{current.title}</CardTitle>
          <CardDescription>{current.description}</CardDescription>
          <div className="mt-3">
            <Progress value={progress} className="h-1.5" />
            <p className="text-xs text-muted-foreground mt-1">Step {step + 1} of {steps.length}</p>
          </div>
        </CardHeader>
        <CardContent>
          {step === 0 && (
            <form id="basic-form" onSubmit={handleSubmit(handleBasicSubmit)} className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Professional Headline</label>
                <Input placeholder="e.g. Senior Software Engineer" {...register('headline')} />
                {errors.headline && <p className="text-xs text-error">{errors.headline.message}</p>}
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Location</label>
                <Input placeholder="e.g. San Francisco, CA" {...register('location')} />
                {errors.location && <p className="text-xs text-error">{errors.location.message}</p>}
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Phone (optional)</label>
                <Input placeholder="e.g. +1 555 123 4567" {...register('phone')} />
              </div>
            </form>
          )}

          {step === 1 && (
            <div className="space-y-3 text-center py-4">
              <p className="text-sm text-muted-foreground">What type of role are you looking for?</p>
              <div className="grid grid-cols-1 gap-2">
                {['Full-time', 'Part-time', 'Contract', 'Remote', 'Hybrid'].map(type => (
                  <button key={type} onClick={() => setStep(s => s + 1)}
                    className="w-full rounded-lg border border-glass-border bg-dark-800 px-4 py-3 text-sm hover:bg-white/5 transition-colors text-left"
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-3 text-center py-4">
              <p className="text-sm text-muted-foreground mb-3">Add your key skills (you can add more later)</p>
              <div className="flex flex-wrap justify-center gap-2">
                {['JavaScript', 'Python', 'React', 'TypeScript', 'Node.js', 'SQL', 'AWS', 'Docker', 'Git', 'Agile'].map(skill => (
                  <button key={skill} onClick={() => {}}
                    className="rounded-full border border-glass-border bg-dark-800 px-3 py-1.5 text-xs hover:bg-white/5 transition-colors"
                  >
                    + {skill}
                  </button>
                ))}
              </div>
              <Input placeholder="Or type a custom skill..." className="mt-3" />
            </div>
          )}

          {step === 3 && (
            <div className="text-center py-4">
              <p className="text-sm text-muted-foreground">Add your work experience to highlight your career history.</p>
              <Button variant="outline" className="mt-4" onClick={() => navigate('/profile')}>Add Experience</Button>
            </div>
          )}

          {step === 4 && (
            <div className="text-center py-4">
              <p className="text-sm text-muted-foreground">Add your educational background.</p>
              <Button variant="outline" className="mt-4" onClick={() => navigate('/profile')}>Add Education</Button>
            </div>
          )}

          {step === 5 && (
            <div className="text-center py-4 space-y-4">
              <p className="text-sm text-muted-foreground">Upload an existing resume to get started quickly.</p>
              <label className="flex flex-col items-center gap-2 cursor-pointer rounded-lg border-2 border-dashed border-glass-border p-6 hover:bg-white/5 transition-colors">
                <Upload className="h-8 w-8 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">{uploading ? 'Uploading...' : 'Click to upload resume'}</span>
                <input type="file" accept=".pdf,.docx,.doc" className="hidden" onChange={handleResumeUpload} disabled={uploading} />
              </label>
            </div>
          )}

          {step === 6 && (
            <div className="text-center py-4 space-y-3">
              <p className="text-sm text-muted-foreground">Complete your career profile to get better job matches.</p>
              <Button className="w-full" onClick={() => { navigate('/profile'); onComplete() }}>Complete Profile</Button>
            </div>
          )}

          {step === 7 && (
            <div className="text-center py-4 space-y-3">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-success/20">
                <CheckCircle className="h-6 w-6 text-success" />
              </div>
              <p className="text-sm text-muted-foreground">Your profile is ready. Start searching for jobs and generating applications!</p>
            </div>
          )}
        </CardContent>
        <CardFooter className="flex-col gap-2">
          <div className="flex w-full gap-2">
            {step > 0 && (
              <Button variant="outline" className="flex-1" onClick={() => setStep(s => s - 1)}>Previous</Button>
            )}
            {step === 0 ? (
              <Button type="submit" form="basic-form" className="flex-1" disabled={submitting}>
                {submitting ? 'Saving...' : 'Next'}
              </Button>
            ) : step === 5 ? (
              <Button variant="outline" className="flex-1" onClick={handleSkip}>Skip for now</Button>
            ) : (
              <Button className="flex-1" onClick={handleNext}>
                {isLast ? 'Go to Dashboard' : 'Next'}
              </Button>
            )}
          </div>
          {current.skippable && step !== 5 && (
            <Button variant="ghost" size="sm" onClick={handleSkip}>Skip this step</Button>
          )}
        </CardFooter>
      </Card>
    </div>
  )
}

export function isProfileWizardCompleted(): boolean {
  return localStorage.getItem('profile_wizard_completed') === 'true'
}
