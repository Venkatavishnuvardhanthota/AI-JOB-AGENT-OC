import { useCallback, useState } from 'react'
import { cn } from '@/lib/utils'
import { useToast } from '@/components/ui/toast'
import { Layout, CheckCircle2 } from 'lucide-react'

const TEMPLATES = [
  { id: 'modern', label: 'Modern', desc: 'Clean, sans-serif, ample spacing', font: 'Inter, sans-serif' },
  { id: 'classic', label: 'Classic', desc: 'Traditional serif, elegant layout', font: 'Georgia, serif' },
  { id: 'executive', label: 'Executive', desc: 'Bold headers, impactful statements', font: 'SF Pro, sans-serif' },
  { id: 'technical', label: 'Technical', desc: 'Monospace accents, structured', font: 'JetBrains Mono, monospace' },
  { id: 'minimal', label: 'Minimal', desc: 'Ultra-clean, maximum whitespace', font: 'Inter, sans-serif' },
  { id: 'graduate', label: 'Graduate', desc: 'Modern, youthful, energetic', font: 'Nunito, sans-serif' },
] as const

interface TemplatePanelProps {
  currentTemplate?: string
  onSelect: (templateId: string) => void
}

function TemplatePreview({ template }: { template: typeof TEMPLATES[number] }) {
  return (
    <div className={cn(
      'rounded-lg border border-glass-border p-3 h-24 flex flex-col justify-center transition-colors',
      template.id === 'modern' && 'font-sans',
      template.id === 'classic' && 'font-serif',
      template.id === 'executive' && 'font-sans',
      template.id === 'technical' && 'font-mono',
      template.id === 'minimal' && 'font-sans',
      template.id === 'graduate' && 'font-sans',
    )}>
      <div className={cn(
        'text-xs font-bold mb-1',
        template.id === 'executive' && 'text-lg tracking-wider uppercase',
        template.id === 'graduate' && 'text-sm font-extrabold tracking-tight',
      )}>
        {template.label}
      </div>
      <div className={cn(
        'text-[10px] text-muted-foreground leading-tight',
        template.id === 'classic' && 'italic',
        template.id === 'minimal' && 'uppercase tracking-widest',
      )}>
        Dear Hiring Manager,
      </div>
      <div className={cn(
        'text-[10px] text-muted-foreground mt-0.5 leading-tight line-clamp-1',
        template.id === 'technical' && 'text-[9px]',
      )}>
        I am writing to express my interest...
      </div>
    </div>
  )
}

export function TemplatePanel({ currentTemplate, onSelect }: TemplatePanelProps) {
  const [selected, setSelected] = useState(currentTemplate || 'modern')
  const { addToast } = useToast()

  const handleSelect = useCallback((id: string) => {
    setSelected(id)
    onSelect(id)
    addToast(`Template changed to ${TEMPLATES.find(t => t.id === id)?.label}`, 'success')
  }, [onSelect, addToast])

  return (
    <div className="space-y-3" role="region" aria-label="Cover letter templates">
      <h3 className="text-sm font-semibold flex items-center gap-2">
        <Layout className="h-4 w-4" /> Templates
      </h3>
      <p className="text-xs text-muted-foreground">
        Changing templates preserves your content — only layout and typography change.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {TEMPLATES.map(t => (
          <button
            key={t.id}
            onClick={() => handleSelect(t.id)}
            className={cn(
              'rounded-xl border p-2 text-left transition-all hover:bg-white/5 relative',
              selected === t.id ? 'border-accent bg-accent/5' : 'border-glass-border',
            )}
            aria-label={`Select ${t.label} template`}
            aria-pressed={selected === t.id}
          >
            {selected === t.id && (
              <CheckCircle2 className="absolute top-2 right-2 h-4 w-4 text-accent" />
            )}
            <TemplatePreview template={t} />
            <p className="text-xs text-muted-foreground mt-1 line-clamp-1">{t.desc}</p>
          </button>
        ))}
      </div>
    </div>
  )
}
