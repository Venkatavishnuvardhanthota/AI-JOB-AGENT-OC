import { useState, useCallback } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { applicationGenerationService } from '@/services/application-generation/application-generation'
import type { GenerationRequest } from '@/services/application-generation/types'
import { Wand2, Plus, X } from 'lucide-react'

export function GenerationWizard() {
  const [step, setStep] = useState(0)
  const [request, setRequest] = useState<GenerationRequest>({
    jobId: '', jobTitle: '', companyName: '', companyIndustry: '', companyDescription: '',
    jobDescription: '', requiredSkills: [], preferredSkills: [], experienceLevel: '',
    educationRequired: '', certificationsRequired: [], responsibilities: [],
    salaryRange: null, remote: false, location: '', applicationUrl: null,
  })
  const [skillInput, setSkillInput] = useState('')
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  const update = <K extends keyof GenerationRequest>(key: K, value: GenerationRequest[K]) =>
    setRequest(r => ({ ...r, [key]: value }))

  const addSkill = (field: 'requiredSkills' | 'preferredSkills') => {
    if (skillInput.trim()) {
      update(field, [...request[field], skillInput.trim()])
      setSkillInput('')
    }
  }

  const removeSkill = (field: 'requiredSkills' | 'preferredSkills', idx: number) =>
    update(field, request[field].filter((_, i) => i !== idx))

  const handleGenerate = useCallback(() => {
    setGenerating(true)
    try {
      const pkg = applicationGenerationService.generate(request)
      setResult(`Package generated for ${pkg.jobTitle} at ${pkg.companyName} with ${pkg.metadata.confidenceScore}% confidence.`)
    } catch (err) {
      setResult(`Generation failed: ${err instanceof Error ? err.message : 'Unknown error'}`)
    }
    setGenerating(false)
  }, [request])

  const steps = [
    { label: 'Job Details', content: (
      <div className="space-y-3">
        <div>
          <label className="text-xs text-muted-foreground mb-1 block">Job Title *</label>
          <Input value={request.jobTitle} onChange={e => update('jobTitle', e.target.value)} placeholder="e.g., Senior Software Engineer" />
        </div>
        <div>
          <label className="text-xs text-muted-foreground mb-1 block">Company Name *</label>
          <Input value={request.companyName} onChange={e => update('companyName', e.target.value)} placeholder="e.g., Acme Corp" />
        </div>
        <div>
          <label className="text-xs text-muted-foreground mb-1 block">Industry</label>
          <Input value={request.companyIndustry} onChange={e => update('companyIndustry', e.target.value)} placeholder="e.g., Technology, Finance, Healthcare" />
        </div>
        <div>
          <label className="text-xs text-muted-foreground mb-1 block">Job Description</label>
          <textarea
            className="w-full min-h-[100px] rounded-lg border border-glass-border bg-dark-800 p-3 text-sm resize-y"
            value={request.jobDescription} onChange={e => update('jobDescription', e.target.value)}
            placeholder="Paste the full job description here..."
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground mb-1 block">Experience Level</label>
          <Input value={request.experienceLevel} onChange={e => update('experienceLevel', e.target.value)} placeholder="e.g., 5, Senior, Lead" />
        </div>
        <div>
          <label className="text-xs text-muted-foreground mb-1 block">Education Required</label>
          <Input value={request.educationRequired} onChange={e => update('educationRequired', e.target.value)} placeholder="e.g., Bachelor's in Computer Science" />
        </div>
      </div>
    )},
    { label: 'Skills & Requirements', content: (
      <div className="space-y-4">
        <div>
          <label className="text-xs text-muted-foreground mb-1 block">Required Skills</label>
          <div className="flex gap-2 mb-2">
            <Input value={skillInput} onChange={e => setSkillInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addSkill('requiredSkills') } }}
              placeholder="Type a skill and press Enter" />
            <Button size="sm" variant="secondary" onClick={() => addSkill('requiredSkills')}><Plus className="h-4 w-4" /></Button>
          </div>
          <div className="flex flex-wrap gap-1">
            {request.requiredSkills.map((s, i) => (
              <Badge key={i} variant="secondary" className="flex items-center gap-1">
                {s} <button onClick={() => removeSkill('requiredSkills', i)}><X className="h-3 w-3" /></button>
              </Badge>
            ))}
          </div>
        </div>
        <div>
          <label className="text-xs text-muted-foreground mb-1 block">Preferred / Nice-to-Have Skills</label>
          <div className="flex gap-2 mb-2">
            <Input value={skillInput} onChange={e => setSkillInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addSkill('preferredSkills') } }}
              placeholder="Type a skill and press Enter" />
            <Button size="sm" variant="secondary" onClick={() => addSkill('preferredSkills')}><Plus className="h-4 w-4" /></Button>
          </div>
          <div className="flex flex-wrap gap-1">
            {request.preferredSkills.map((s, i) => (
              <Badge key={i} variant="outline" className="flex items-center gap-1">
                {s} <button onClick={() => removeSkill('preferredSkills', i)}><X className="h-3 w-3" /></button>
              </Badge>
            ))}
          </div>
        </div>
        <div>
          <label className="text-xs text-muted-foreground mb-1 block">Certifications Required (one per line)</label>
          <textarea
            className="w-full min-h-[60px] rounded-lg border border-glass-border bg-dark-800 p-3 text-sm resize-y"
            value={request.certificationsRequired.join('\n')}
            onChange={e => update('certificationsRequired', e.target.value.split('\n').filter(Boolean))}
            placeholder="e.g., AWS Solutions Architect&#10;Google Cloud Professional"
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground mb-1 block">Key Responsibilities (one per line)</label>
          <textarea
            className="w-full min-h-[80px] rounded-lg border border-glass-border bg-dark-800 p-3 text-sm resize-y"
            value={request.responsibilities.join('\n')}
            onChange={e => update('responsibilities', e.target.value.split('\n').filter(Boolean))}
            placeholder="e.g., Design and implement scalable microservices&#10;Lead code reviews and mentor junior engineers"
          />
        </div>
      </div>
    )},
    { label: 'Generate', content: (
      <div className="space-y-4">
        <Card className="p-4 bg-dark-800/50">
          <h4 className="text-sm font-medium mb-2">Review & Generate</h4>
          <div className="space-y-1 text-sm text-muted-foreground">
            <p>Job: <span className="text-foreground">{request.jobTitle || 'Not specified'}</span></p>
            <p>Company: <span className="text-foreground">{request.companyName || 'Not specified'}</span></p>
            <p>Industry: <span className="text-foreground">{request.companyIndustry || 'Not specified'}</span></p>
            <p>Required Skills: <span className="text-foreground">{request.requiredSkills.length} skills</span></p>
            <p>Preferred Skills: <span className="text-foreground">{request.preferredSkills.length} skills</span></p>
          </div>
        </Card>
        <Button
          className="w-full"
          onClick={handleGenerate}
          disabled={generating || !request.jobTitle || !request.companyName}
        >
          <Wand2 className="h-4 w-4 mr-1" />
          {generating ? 'Generating...' : 'Generate Application Package'}
        </Button>
        {result && (
          <Card className={`p-3 text-sm ${result.includes('failed') ? 'bg-error/10 text-error' : 'bg-success/10 text-success'}`}>
            {result}
          </Card>
        )}
      </div>
    )},
  ]

  return (
    <div className="space-y-4">
      <div className="flex gap-1 border-b border-glass-border mb-4">
        {steps.map((s, i) => (
          <button
            key={s.label}
            onClick={() => setStep(i)}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              step === i ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {i + 1}. {s.label}
          </button>
        ))}
      </div>
      {steps[step].content}
      <div className="flex justify-between pt-2">
        <Button variant="ghost" size="sm" disabled={step === 0} onClick={() => setStep(s => s - 1)}>Previous</Button>
        <Button size="sm" disabled={step === steps.length - 1} onClick={() => setStep(s => s + 1)}>Next</Button>
      </div>
    </div>
  )
}
