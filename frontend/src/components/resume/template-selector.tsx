import { useResumeTemplates } from '@/api/hooks'
import { cn } from '@/lib/utils'
import { Check } from 'lucide-react'

interface TemplateSelectorProps {
  value: string
  onChange: (value: string) => void
}

const defaultTemplates = [
  { id: '', name: 'Modern', description: 'Clean two-column layout' },
  { id: 'professional', name: 'Professional', description: 'Traditional single-column' },
  { id: 'simple-ats', name: 'Simple ATS', description: 'ATS-optimized minimal' },
  { id: 'technical', name: 'Technical', description: 'Skills-focused layout' },
]

export function TemplateSelector({ value, onChange }: TemplateSelectorProps) {
  const { data: customTemplates } = useResumeTemplates() as any
  const allTemplates = [
    ...defaultTemplates,
    ...((customTemplates || []).map((t: any) => ({ id: t.name, name: t.name, description: '' }))),
  ]

  return (
    <div className="grid grid-cols-2 gap-3" role="radiogroup" aria-label="Resume template">
      {allTemplates.map((t) => (
        <button
          key={t.id}
          type="button"
          role="radio"
          aria-checked={value === t.id}
          onClick={() => onChange(t.id)}
          className={cn(
            "relative rounded-lg border p-3 text-left transition-all hover:bg-white/5 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary",
            value === t.id
              ? "border-primary bg-primary/5"
              : "border-glass-border"
          )}
        >
          {value === t.id && (
            <Check className="absolute top-2 right-2 h-4 w-4 text-primary" aria-hidden="true" />
          )}
          <p className="text-sm font-medium">{t.name}</p>
          {t.description && (
            <p className="text-xs text-muted-foreground mt-0.5">{t.description}</p>
          )}
        </button>
      ))}
    </div>
  )
}
