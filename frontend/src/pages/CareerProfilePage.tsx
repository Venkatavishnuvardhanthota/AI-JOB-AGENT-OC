import { useEffect, useMemo, useState } from 'react'
import {
  useProfile, useUpdateProfile, useProfileSection, useCreateProfileSection,
  useUpdateProfileSection, useDeleteProfileSection, useProfileCompleteness,
  useReplaceSkills,
} from '@/api/hooks'
import type { ProfileCompleteness } from '@/types'
import { PageHeader } from '@/components/layout/page-header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { useToast } from '@/components/ui/toast'
import {
  UserCircle, Plus, Pencil, Trash2, GraduationCap, Briefcase, Wrench,
  FolderGit2, Award, Languages, Link as LinkIcon, Trophy, ExternalLink,
  Loader2, X,
} from 'lucide-react'
import { cn } from '@/lib/utils'

type FieldType = 'text' | 'url' | 'number' | 'date' | 'textarea' | 'select' | 'checkbox' | 'list'

interface FieldDef {
  key: string
  label: string
  type?: FieldType
  options?: { value: string; label: string }[]
  placeholder?: string
  full?: boolean
  required?: boolean
  step?: string
  help?: string
}

const ACHIEVEMENT_TYPE_OPTIONS = [
  'Award',
  'Certificate',
  'Badge',
  'Certification',
  'Competition',
  'Hackathon',
  'Scholarship',
  'Publication',
  'Patent',
  'Research',
  'Open Source',
  'Employee Recognition',
  'Leadership',
  'Volunteer',
  'Other',
]

const SKILL_SUGGESTIONS = [
  'Python', 'JavaScript', 'TypeScript', 'Java', 'Go', 'Rust', 'C++', 'C#', 'SQL',
  'React', 'Vue', 'Angular', 'Node.js', 'Django', 'Flask', 'FastAPI', 'Express',
  'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Docker', 'Kubernetes', 'AWS', 'GCP',
  'Azure', 'Git', 'GitHub Actions', 'CI/CD', 'Machine Learning', 'Deep Learning',
  'TensorFlow', 'PyTorch', 'REST APIs', 'GraphQL', 'System Design',
  'Agile', 'Scrum', 'Communication', 'Leadership', 'Project Management',
]

function addSkillTag(tags: string[], raw: string): { tags: string[]; added: boolean } {
  const name = raw.trim().replace(/,+$/, '').trim()
  if (!name) return { tags, added: false }
  if (tags.some(t => t.toLowerCase() === name.toLowerCase())) return { tags, added: false }
  return { tags: [...tags, name], added: true }
}

interface SectionConfig {
  key: string
  label: string
  icon: typeof Wrench
  addLabel: string
  fields: FieldDef[]
}

const sections: SectionConfig[] = [
  {
    key: 'education', label: 'Education', icon: GraduationCap, addLabel: 'Add education',
    fields: [
      { key: 'institution', label: 'Institution', required: true },
      { key: 'degree', label: 'Degree', required: true },
      { key: 'field_of_study', label: 'Field of Study' },
      { key: 'location', label: 'Location' },
      { key: 'cgpa', label: 'CGPA' },
      { key: 'start_date', label: 'Start Date', type: 'date' },
      { key: 'end_date', label: 'End Date', type: 'date' },
      { key: 'currently_studying', label: 'Currently studying here', type: 'checkbox' },
    ],
  },
  {
    key: 'experience', label: 'Experience', icon: Briefcase, addLabel: 'Add experience',
    fields: [
      { key: 'title', label: 'Job Title', required: true },
      { key: 'company', label: 'Company', required: true },
      { key: 'location', label: 'Location' },
      { key: 'employment_type', label: 'Employment Type', type: 'select', options: [
        { value: 'full_time', label: 'Full-time' },
        { value: 'part_time', label: 'Part-time' },
        { value: 'contract', label: 'Contract' },
        { value: 'freelance', label: 'Freelance' },
        { value: 'internship', label: 'Internship' },
      ] },
      { key: 'start_date', label: 'Start Date', type: 'date' },
      { key: 'end_date', label: 'End Date', type: 'date' },
      { key: 'currently_working', label: 'I currently work here', type: 'checkbox' },
      { key: 'responsibilities', label: 'Responsibilities', type: 'list', full: true, placeholder: 'One per line' },
      { key: 'achievements', label: 'Key Achievements', type: 'list', full: true, placeholder: 'One per line' },
      { key: 'technologies_used', label: 'Technologies Used', type: 'list', full: true, placeholder: 'One per line' },
    ],
  },
  {
    key: 'projects', label: 'Projects', icon: FolderGit2, addLabel: 'Add project',
    fields: [
      { key: 'name', label: 'Project Name', required: true },
      { key: 'description', label: 'Description', type: 'textarea', full: true },
      { key: 'technologies', label: 'Technologies', type: 'list', placeholder: 'One per line' },
      { key: 'github_url', label: 'GitHub URL', type: 'url' },
      { key: 'demo_url', label: 'Demo URL', type: 'url' },
      { key: 'live_url', label: 'Live URL', type: 'url' },
      { key: 'start_date', label: 'Start Date', type: 'date' },
      { key: 'end_date', label: 'End Date', type: 'date' },
    ],
  },
  {
    key: 'certifications', label: 'Certifications', icon: Award, addLabel: 'Add certification',
    fields: [
      { key: 'name', label: 'Certification Name', required: true },
      { key: 'issuer', label: 'Issuer' },
      { key: 'credential_id', label: 'Credential ID' },
      { key: 'credential_url', label: 'Credential URL', type: 'url' },
      { key: 'issue_date', label: 'Issue Date', type: 'date' },
      { key: 'expiration_date', label: 'Expiration Date', type: 'date' },
    ],
  },
  {
    key: 'languages', label: 'Languages', icon: Languages, addLabel: 'Add language',
    fields: [
      { key: 'language', label: 'Language', required: true, placeholder: 'e.g. English' },
      { key: 'proficiency', label: 'Proficiency', type: 'select', options: [
        { value: 'Beginner', label: 'Beginner' },
        { value: 'Intermediate', label: 'Intermediate' },
        { value: 'Advanced', label: 'Advanced' },
        { value: 'Fluent', label: 'Fluent' },
        { value: 'Native', label: 'Native' },
      ] },
    ],
  },
  {
    key: 'social-links', label: 'Social Links', icon: LinkIcon, addLabel: 'Add link',
    fields: [
      { key: 'platform', label: 'Platform', type: 'select', required: true, options: [
        { value: 'linkedin', label: 'LinkedIn' },
        { value: 'github', label: 'GitHub' },
        { value: 'portfolio', label: 'Portfolio' },
        { value: 'website', label: 'Personal Website' },
        { value: 'other', label: 'Other' },
      ] },
      { key: 'url', label: 'URL', type: 'url', required: true, placeholder: 'https://...' },
    ],
  },
  {
    key: 'achievements', label: 'Achievements', icon: Trophy, addLabel: 'Add achievement',
    fields: [
      { key: 'title', label: 'Title', required: true, placeholder: 'e.g. Won regional hackathon' },
      { key: 'organization', label: 'Organization' },
      { key: 'achievement_type', label: 'Type', type: 'select', options: ACHIEVEMENT_TYPE_OPTIONS.map(value => ({ value, label: value })) },
      { key: 'date', label: 'Date', type: 'date' },
      { key: 'description', label: 'Description', type: 'textarea', full: true },
      { key: 'url', label: 'URL', type: 'url' },
    ],
  },
]

const personalFields: FieldDef[] = [
  { key: 'headline', label: 'Headline', placeholder: 'e.g. Senior Software Engineer' },
  { key: 'current_role', label: 'Current Role', placeholder: 'e.g. Software Engineer' },
  { key: 'desired_role', label: 'Desired Role', placeholder: 'e.g. Senior Backend Engineer' },
  {
    key: 'employment_status', label: 'Employment Status', type: 'select',
    options: [
      { value: 'employed', label: 'Employed' },
      { value: 'self_employed', label: 'Self-employed' },
      { value: 'freelancer', label: 'Freelancer' },
      { value: 'student', label: 'Student' },
      { value: 'unemployed', label: 'Unemployed' },
      { value: 'retired', label: 'Retired' },
      { value: 'other', label: 'Other' },
    ],
  },
  { key: 'total_years_experience', label: 'Total Years of Experience', type: 'number', step: '0.5' },
  { key: 'notice_period', label: 'Notice Period', placeholder: 'e.g. 30 days' },
  { key: 'current_salary', label: 'Current Salary', type: 'number' },
  { key: 'expected_salary', label: 'Expected Salary', type: 'number' },
  {
    key: 'salary_preference', label: 'Salary Preference', type: 'select',
    options: [
      { value: 'paid_only', label: 'Paid only' },
      { value: 'paid_preferred', label: 'Paid preferred, unpaid considered' },
      { value: 'unpaid_acceptable', label: 'Open to unpaid' },
    ],
  },
  { key: 'willing_to_relocate', label: 'Willing to relocate', type: 'checkbox' },
  { key: 'visa_sponsorship_requirement', label: 'Requires visa sponsorship', type: 'checkbox' },
  { key: 'portfolio_url', label: 'Portfolio URL', type: 'url' },
  { key: 'linkedin_url', label: 'LinkedIn URL', type: 'url' },
  { key: 'github_url', label: 'GitHub URL', type: 'url' },
  { key: 'website_url', label: 'Website URL', type: 'url' },
  { key: 'professional_summary', label: 'Professional Summary', type: 'textarea', full: true, placeholder: 'Tell recruiters about your experience and strengths...' },
]

const SALARY_PREFERENCE_LABELS: Record<string, string> = {
  paid_only: 'Paid only',
  paid_preferred: 'Paid preferred, unpaid considered',
  unpaid_acceptable: 'Open to unpaid',
}

const EMPLOYMENT_STATUS_LABELS: Record<string, string> = {
  employed: 'Employed',
  self_employed: 'Self-employed',
  freelancer: 'Freelancer',
  student: 'Student',
  unemployed: 'Unemployed',
  retired: 'Retired',
  other: 'Other',
}

function splitList(value: string): string[] {
  return value
    .split(/[\n,]/)
    .map(v => v.trim())
    .filter(Boolean)
}

function buildPayload(fields: FieldDef[], form: Record<string, any>): Record<string, any> {
  const payload: Record<string, any> = {}
  for (const field of fields) {
    const raw = form[field.key]
    switch (field.type) {
      case 'number': {
        const value = String(raw ?? '').trim()
        if (value !== '') payload[field.key] = Number(value)
        break
      }
      case 'date': {
        const value = String(raw ?? '').trim()
        if (value !== '') payload[field.key] = value
        break
      }
      case 'checkbox':
        payload[field.key] = !!raw
        break
      case 'list': {
        const value = splitList(String(raw ?? ''))
        if (value.length > 0) payload[field.key] = value
        break
      }
      default: {
        const value = String(raw ?? '').trim()
        if (value !== '') payload[field.key] = value
      }
    }
  }
  return payload
}

function formFromItem(fields: FieldDef[], item: Record<string, any> | null): Record<string, any> {
  const form: Record<string, any> = {}
  for (const field of fields) {
    const value = item?.[field.key]
    if (field.type === 'list' && Array.isArray(value)) form[field.key] = value.join('\n')
    else if (value !== undefined && value !== null) form[field.key] = value
    else form[field.key] = ''
  }
  return form
}

function formatDate(value: string | null | undefined): string {
  if (!value) return ''
  const [y, m] = value.split('-')
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  const month = months[Number(m) - 1]
  return month ? `${month} ${y}` : value
}

interface Summary {
  title: string
  subtitle: string
  meta: string[]
  url?: string
}

function summaryOf(section: string, item: Record<string, any>): Summary {
  switch (section) {
    case 'education': {
      const meta = [
        item.location,
        item.start_date || item.end_date ? `${formatDate(item.start_date)} – ${formatDate(item.end_date) || 'Present'}` : '',
        item.cgpa ? `CGPA: ${item.cgpa}` : '',
      ].filter(Boolean)
      return { title: `${item.degree || ''}${item.institution ? ` at ${item.institution}` : ''}` || item.institution, subtitle: item.field_of_study || '', meta }
    }
    case 'experience': {
      const meta = [
        item.location,
        item.employment_type?.replace('_', ' '),
        item.start_date || item.end_date ? `${formatDate(item.start_date)} – ${formatDate(item.end_date) || 'Present'}` : '',
      ].filter(Boolean)
      return { title: `${item.title || ''}${item.company ? ` at ${item.company}` : ''}` || item.company, subtitle: '', meta }
    }
    case 'projects': {
      return {
        title: item.name,
        subtitle: item.description || '',
        meta: [
          Array.isArray(item.technologies) ? item.technologies.join(', ') : '',
          item.start_date || item.end_date ? `${formatDate(item.start_date)} – ${formatDate(item.end_date) || 'Present'}` : '',
        ].filter(Boolean),
        url: item.demo_url || item.live_url || item.github_url || undefined,
      }
    }
    case 'certifications': {
      return {
        title: item.name,
        subtitle: item.issuer || '',
        meta: [
          item.issue_date ? `Issued ${formatDate(item.issue_date)}` : '',
          item.expiration_date ? `Expires ${formatDate(item.expiration_date)}` : '',
          item.credential_id,
        ].filter(Boolean),
        url: item.credential_url || undefined,
      }
    }
    case 'languages':
      return { title: item.language, subtitle: '', meta: item.proficiency ? [item.proficiency] : [] }
    case 'social-links':
      return { title: item.title || item.platform, subtitle: '', meta: [], url: item.url }
    case 'achievements': {
      return {
        title: item.title,
        subtitle: item.description || '',
        meta: [item.organization, item.achievement_type, item.date ? formatDate(item.date) : ''].filter(Boolean),
        url: item.url || undefined,
      }
    }
    default:
      return { title: item.name || item.title || '', subtitle: '', meta: [] }
  }
}

function FieldInput({ field, value, onChange }: {
  field: FieldDef
  value: any
  onChange: (key: string, value: any) => void
}) {
  const id = `field-${field.key}`
  const common = `w-full rounded-md border border-glass-border bg-dark-900 px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary`

  if (field.type === 'checkbox') {
    return (
      <label htmlFor={id} className="flex items-center gap-2 text-sm cursor-pointer select-none">
        <input
          id={id}
          type="checkbox"
          checked={!!value}
          onChange={e => onChange(field.key, e.target.checked)}
          className="h-4 w-4 rounded border-glass-border bg-dark-800 accent-primary"
        />
        {field.label}
      </label>
    )
  }
  if (field.type === 'select') {
    return (
      <div className={cn(field.full && 'md:col-span-2')}>
        <label htmlFor={id} className="text-xs text-muted-foreground block mb-1">{field.label}{field.required && <span className="text-error ml-0.5">*</span>}</label>
        <select
          id={id}
          value={value || ''}
          onChange={e => onChange(field.key, e.target.value)}
          className={cn(common, 'bg-dark-900')}
        >
          <option value="">Select...</option>
          {field.options?.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </div>
    )
  }
  if (field.type === 'textarea' || field.type === 'list') {
    return (
      <div className={cn(field.full && 'md:col-span-2')}>
        <label htmlFor={id} className="text-xs text-muted-foreground block mb-1">{field.label}{field.required && <span className="text-error ml-0.5">*</span>}</label>
        <textarea
          id={id}
          value={value || ''}
          onChange={e => onChange(field.key, e.target.value)}
          placeholder={field.placeholder}
          className={cn(common, 'min-h-[64px]')}
        />
        {field.type === 'list' && field.help && <p className="text-xs text-muted-foreground mt-1">{field.help}</p>}
      </div>
    )
  }
  return (
    <div className={cn(field.full && 'md:col-span-2')}>
      <label htmlFor={id} className="text-xs text-muted-foreground block mb-1">{field.label}{field.required && <span className="text-error ml-0.5">*</span>}</label>
      <Input
        id={id}
        type={field.type === 'number' ? 'number' : field.type === 'date' ? 'date' : 'text'}
        inputMode={field.type === 'number' ? 'decimal' : undefined}
        step={field.step}
        value={value || ''}
        onChange={e => onChange(field.key, e.target.value)}
        placeholder={field.placeholder}
      />
    </div>
  )
}

function AchievementTypeField({ value, onChange }: {
  value: any
  onChange: (key: string, value: any) => void
}) {
  const id = 'field-achievement_type'
  const isPreset = ACHIEVEMENT_TYPE_OPTIONS.includes(value)
  const showCustom = value === 'Other' || (!!value && !isPreset)
  const common = `w-full rounded-md border border-glass-border bg-dark-900 px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary`
  return (
    <div className="md:col-span-2 space-y-2">
      <label htmlFor={id} className="text-xs text-muted-foreground block mb-1">Type</label>
      <select
        id={id}
        value={showCustom ? 'Other' : (value || '')}
        onChange={e => onChange('achievement_type', e.target.value)}
        className={common}
      >
        <option value="">Select...</option>
        {ACHIEVEMENT_TYPE_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
      {showCustom && (
        <Input
          id="field-achievement_type_custom"
          type="text"
          value={value === 'Other' ? '' : value}
          onChange={e => onChange('achievement_type', e.target.value)}
          placeholder="Enter custom type"
        />
      )}
    </div>
  )
}

function SectionModal({ config, item, onClose, onSaved }: {
  config: SectionConfig
  item: Record<string, any> | null
  onClose: () => void
  onSaved: () => void
}) {
  const createItem = useCreateProfileSection(config.key)
  const updateItem = useUpdateProfileSection(config.key)
  const { addToast } = useToast()
  const [form, setForm] = useState<Record<string, any>>(() => formFromItem(config.fields, item))
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const saving = createItem.isPending || updateItem.isPending

  const handleSubmit = async () => {
    const missing = config.fields.find(f => f.required && !String(form[f.key] ?? '').trim())
    if (missing) {
      setError(`${missing.label} is required.`)
      return
    }
    if (config.key === 'achievements' && form.achievement_type === 'Other') {
      setError('Please enter a custom type.')
      return
    }
    const payload = buildPayload(config.fields, form)
    setError(null)
    try {
      if (item?.id) {
        await updateItem.mutateAsync({ id: item.id, data: payload })
        addToast(`${config.label} updated`, 'success')
      } else {
        await createItem.mutateAsync(payload)
        addToast(`${config.label} added`, 'success')
      }
      onSaved()
    } catch (err: any) {
      setError(err?.message || `Failed to save ${config.label.toLowerCase()}`)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="section-modal-title"
        className="w-full max-w-lg max-h-[85vh] overflow-y-auto rounded-xl border border-glass-border bg-dark-900 p-6 shadow-xl"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 id="section-modal-title" className="text-lg font-semibold">
            {item ? `Edit ${config.label}` : `Add ${config.label}`}
          </h3>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close dialog">
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {config.fields.map(field => (
            config.key === 'achievements' && field.key === 'achievement_type' ? (
              <AchievementTypeField
                key={field.key}
                value={form[field.key]}
                onChange={(key, value) => setForm(prev => ({ ...prev, [key]: value }))}
              />
            ) : (
              <FieldInput
                key={field.key}
                field={field}
                value={form[field.key]}
                onChange={(key, value) => setForm(prev => ({ ...prev, [key]: value }))}
              />
            )
          ))}
        </div>

        {error && (
          <p className="mt-4 text-sm text-error" role="alert">{error}</p>
        )}

        <div className="flex justify-end gap-2 mt-5">
          <Button variant="outline" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={saving}>
            {saving && <Loader2 className="h-4 w-4 mr-1 animate-spin" aria-hidden="true" />}
            {item ? 'Update' : 'Add'}
          </Button>
        </div>
      </div>
    </div>
  )
}

function SectionCard({ config }: { config: SectionConfig }) {
  const { data: items, isLoading, isError, refetch } = useProfileSection<any>(config.key)
  const deleteItem = useDeleteProfileSection(config.key)
  const { addToast } = useToast()
  const [modal, setModal] = useState<{ open: boolean; item: Record<string, any> | null }>({ open: false, item: null })
  const Icon = config.icon
  const list = Array.isArray(items) ? items : []
  const count = list.length

  const handleDelete = async (item: Record<string, any>) => {
    if (!window.confirm(`Delete this ${config.label.toLowerCase()}? This cannot be undone.`)) return
    try {
      await deleteItem.mutateAsync(item.id)
      addToast(`${config.label} deleted`, 'info')
    } catch (err: any) {
      addToast(err?.message || 'Failed to delete', 'error')
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="flex items-center gap-2">
            <Icon className="h-5 w-5 text-primary shrink-0" />
            <span>{config.label}</span>
            {count > 0 && (
              <span className="text-xs font-normal text-muted-foreground" aria-label={`${count} ${config.label.toLowerCase()}`}>
                {count}
              </span>
            )}
          </CardTitle>
          <Button variant="outline" size="sm" onClick={() => setModal({ open: true, item: null })}>
            <Plus className="h-4 w-4 mr-1" /> Add
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-16 w-full" />
        ) : isError ? (
          <div className="flex flex-col items-center justify-center py-8 text-center" role="alert">
            <p className="text-sm text-muted-foreground">Couldn't load {config.label.toLowerCase()}. Please try again.</p>
            <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()}>
              Retry
            </Button>
          </div>
        ) : count === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Icon className="h-8 w-8 text-muted-foreground/40 mb-2" aria-hidden="true" />
            <p className="text-sm text-muted-foreground">No {config.label.toLowerCase()} added yet.</p>
            <Button variant="outline" size="sm" className="mt-3" onClick={() => setModal({ open: true, item: null })}>
              <Plus className="h-4 w-4 mr-1" /> {config.addLabel}
            </Button>
          </div>
        ) : (
          <ul className="space-y-2">
            {list.map((item: any) => {
              const summary = summaryOf(config.key, item)
              return (
                <li key={item.id} className="flex items-start justify-between gap-3 p-3 rounded-lg bg-dark-800/30 hover:bg-dark-800/50">
                  <div className="min-w-0">
                    <p className="text-sm font-medium flex items-center gap-1.5">
                      <span className="truncate">{summary.title}</span>
                      {summary.url && (
                        <a href={summary.url} target="_blank" rel="noopener noreferrer" aria-label={`Open ${summary.title}`} className="text-primary hover:underline inline-flex shrink-0">
                          <ExternalLink className="h-3.5 w-3.5" />
                        </a>
                      )}
                    </p>
                    {summary.subtitle && <p className="text-xs text-muted-foreground truncate">{summary.subtitle}</p>}
                    {summary.meta.length > 0 && (
                      <p className="text-xs text-muted-foreground/80 truncate">{summary.meta.join(' · ')}</p>
                    )}
                  </div>
                  <div className="flex gap-1 shrink-0">
                    <Button variant="ghost" size="sm" onClick={() => setModal({ open: true, item })} aria-label={`Edit ${summary.title}`}>
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => handleDelete(item)} aria-label={`Delete ${summary.title}`}>
                      <Trash2 className="h-4 w-4 text-error" />
                    </Button>
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </CardContent>

      {modal.open && (
        <SectionModal
          config={config}
          item={modal.item}
          onClose={() => setModal({ open: false, item: null })}
          onSaved={() => setModal({ open: false, item: null })}
        />
      )}
    </Card>
  )
}

function SkillsCard() {
  const { data: items, isLoading, isError, refetch } = useProfileSection<any>('skills')
  const replaceSkills = useReplaceSkills()
  const { addToast } = useToast()
  const [tags, setTags] = useState<string[]>([])
  const [input, setInput] = useState('')
  const [dirty, setDirty] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const list = Array.isArray(items) ? items : []

  useEffect(() => {
    if (!dirty && Array.isArray(items)) {
      setTags(items.map((s: any) => s.name))
    }
  }, [items, dirty])

  const handleAdd = () => {
    const parts = input.split(',').map(p => p.trim()).filter(Boolean)
    if (parts.length === 0) return
    let next = tags
    let addedAny = false
    for (const part of parts) {
      const result = addSkillTag(next, part)
      if (result.added) {
        next = result.tags
        addedAny = true
      }
    }
    if (addedAny) {
      setTags(next)
      setDirty(true)
      setError(null)
    } else {
      setError(`"${parts.join(', ')}" is already in your skills.`)
    }
    setInput('')
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleAdd()
    } else if (e.key === 'Backspace' && input === '' && tags.length > 0) {
      setTags(tags.slice(0, -1))
      setDirty(true)
    }
  }

  const handleSave = async () => {
    if (tags.length === 0) {
      setError('Add at least one skill.')
      return
    }
    setError(null)
    try {
      await replaceSkills.mutateAsync(tags)
      addToast('Skills saved', 'success')
      setDirty(false)
    } catch (err: any) {
      setError(err?.message || 'Failed to save skills')
    }
  }

  const handleDiscard = () => {
    if (Array.isArray(items)) setTags(items.map((s: any) => s.name))
    setDirty(false)
    setError(null)
    setInput('')
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="flex items-center gap-2">
            <Wrench className="h-5 w-5 text-primary shrink-0" />
            <span>Skills</span>
            {list.length > 0 && (
              <span className="text-xs font-normal text-muted-foreground" aria-label={`${list.length} skills`}>
                {list.length}
              </span>
            )}
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-16 w-full" />
        ) : isError ? (
          <div className="flex flex-col items-center justify-center py-8 text-center" role="alert">
            <p className="text-sm text-muted-foreground">Couldn't load skills. Please try again.</p>
            <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()}>
              Retry
            </Button>
          </div>
        ) : (
          <>
            <div className="flex flex-wrap gap-2 mb-3" aria-label="Selected skills">
              {tags.length === 0 ? (
                <p className="text-sm text-muted-foreground">No skills added yet. Type a skill below and press Enter.</p>
              ) : (
                tags.map(tag => (
                  <span key={tag} className="inline-flex items-center gap-1 rounded-full border border-glass-border bg-dark-800 px-3 py-1 text-sm">
                    {tag}
                    <button
                      type="button"
                      onClick={() => { setTags(tags.filter(t => t !== tag)); setDirty(true) }}
                      aria-label={`Remove ${tag}`}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </span>
                ))
              )}
            </div>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Input
                  value={input}
                  onChange={e => { setInput(e.target.value); if (error) setError(null) }}
                  onKeyDown={handleKeyDown}
                  placeholder="Type a skill and press Enter..."
                  list="skill-suggestions"
                  aria-label="Add skill"
                />
                <datalist id="skill-suggestions">
                  {SKILL_SUGGESTIONS.map(s => <option key={s} value={s} />)}
                </datalist>
              </div>
              <Button variant="outline" onClick={handleAdd}>Add</Button>
            </div>
            {error && (
              <p className="mt-2 text-sm text-error" role="alert">{error}</p>
            )}
            {dirty ? (
              <div className="flex justify-end gap-2 mt-3">
                <Button variant="outline" size="sm" onClick={handleDiscard} disabled={replaceSkills.isPending}>
                  Discard
                </Button>
                <Button size="sm" onClick={handleSave} disabled={replaceSkills.isPending || tags.length === 0}>
                  {replaceSkills.isPending && <Loader2 className="h-4 w-4 mr-1 animate-spin" aria-hidden="true" />}
                  {replaceSkills.isPending ? 'Saving…' : 'Save skills'}
                </Button>
              </div>
            ) : (
              list.length > 0 && (
                <p className="mt-2 text-xs text-muted-foreground">Saved {list.length} {list.length === 1 ? 'skill' : 'skills'}</p>
              )
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}

export function CareerProfilePage() {
  const { data: profile, isLoading: profileLoading } = useProfile()
  const { data: completeness } = useProfileCompleteness()
  const updateProfile = useUpdateProfile()
  const { addToast } = useToast()

  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState<Record<string, any>>({})
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (profile) {
      setForm(formFromItem(personalFields, profile as unknown as Record<string, any>))
    }
  }, [profile])

  const handleSaveProfile = async () => {
    const payload = buildPayload(personalFields, form)
    setError(null)
    try {
      await updateProfile.mutateAsync(payload)
      addToast('Profile details updated', 'success')
      setEditing(false)
    } catch (err: any) {
      setError(err?.message || 'Failed to update profile')
    }
  }

  const percent = useMemo(() => {
    const data = completeness as ProfileCompleteness | undefined
    if (data && typeof data.percentage === 'number') return data.percentage
    return null
  }, [completeness])

  if (profileLoading) return (
    <div className="space-y-6 max-w-5xl">
      <Skeleton className="h-8 w-56" />
      <Skeleton className="h-56 rounded-xl" />
      {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-32 rounded-xl" />)}
    </div>
  )

  const detailRows = [
    { label: 'Headline', value: profile?.headline },
    { label: 'Current Role', value: profile?.current_role },
    { label: 'Desired Role', value: profile?.desired_role },
    { label: 'Employment Status', value: profile?.employment_status ? EMPLOYMENT_STATUS_LABELS[profile.employment_status] || profile.employment_status : null },
    { label: 'Total Experience', value: profile?.total_years_experience != null ? `${profile.total_years_experience} years` : null },
    { label: 'Notice Period', value: profile?.notice_period },
    { label: 'Current Salary', value: profile?.current_salary != null ? `$${Number(profile.current_salary).toLocaleString()}` : null },
    { label: 'Expected Salary', value: profile?.expected_salary != null ? `$${Number(profile.expected_salary).toLocaleString()}` : null },
    { label: 'Salary Preference', value: profile?.salary_preference ? SALARY_PREFERENCE_LABELS[profile.salary_preference] || profile.salary_preference : null },
    { label: 'Willing to Relocate', value: profile?.willing_to_relocate == null ? null : profile.willing_to_relocate ? 'Yes' : 'No' },
    { label: 'Visa Sponsorship', value: profile?.visa_sponsorship_requirement == null ? null : profile.visa_sponsorship_requirement ? 'Required' : 'Not required' },
    { label: 'Portfolio', value: profile?.portfolio_url },
    { label: 'LinkedIn', value: profile?.linkedin_url },
    { label: 'GitHub', value: profile?.github_url },
    { label: 'Website', value: profile?.website_url },
  ].filter(row => row.value)

  return (
    <div className="space-y-6 max-w-5xl">
      <PageHeader
        title="Career Profile"
        description={percent != null ? `Profile ${percent}% complete` : 'Manage your career details'}
        actions={
          <Button
            variant={editing ? 'default' : 'outline'}
            onClick={() => editing ? handleSaveProfile() : setEditing(true)}
            disabled={updateProfile.isPending}
          >
            {updateProfile.isPending && <Loader2 className="h-4 w-4 mr-1 animate-spin" aria-hidden="true" />}
            {editing ? (updateProfile.isPending ? 'Saving…' : 'Save') : 'Edit'}
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-2">
            <CardTitle className="flex items-center gap-2">
              <UserCircle className="h-5 w-5 text-primary" />
              Personal Details
            </CardTitle>
            {!editing && (
              <Button variant="ghost" size="sm" onClick={() => setEditing(true)}>
                <Pencil className="h-4 w-4 mr-1" /> Edit
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {editing ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {personalFields.map(field => (
                <FieldInput
                  key={field.key}
                  field={field}
                  value={form[field.key]}
                  onChange={(key, value) => setForm(prev => ({ ...prev, [key]: value }))}
                />
              ))}
              {error && (
                <p className="text-sm text-error md:col-span-2" role="alert">{error}</p>
              )}
              <div className="flex justify-end gap-2 md:col-span-2">
                <Button variant="outline" onClick={() => { setEditing(false); setError(null); if (profile) setForm(formFromItem(personalFields, profile as unknown as Record<string, any>)) }} disabled={updateProfile.isPending}>
                  Cancel
                </Button>
                <Button onClick={handleSaveProfile} disabled={updateProfile.isPending}>
                  {updateProfile.isPending && <Loader2 className="h-4 w-4 mr-1 animate-spin" aria-hidden="true" />}
                  {updateProfile.isPending ? 'Saving…' : 'Save Changes'}
                </Button>
              </div>
            </div>
          ) : detailRows.length === 0 && !profile?.professional_summary ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <UserCircle className="h-8 w-8 text-muted-foreground/40 mb-2" aria-hidden="true" />
              <p className="text-sm text-muted-foreground">No personal details added yet.</p>
              <Button variant="outline" size="sm" className="mt-3" onClick={() => setEditing(true)}>
                <Pencil className="h-4 w-4 mr-1" /> Add your details
              </Button>
            </div>
          ) : (
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-2.5">
              {detailRows.map(row => (
                <div key={row.label} className="flex items-start gap-2 text-sm min-w-0">
                  <dt className="text-muted-foreground shrink-0 min-w-36">{row.label}</dt>
                  <dd className="min-w-0 break-words">
                    {String(row.value).startsWith('http') ? (
                      <a href={String(row.value)} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline inline-flex items-center gap-1">
                        <span className="truncate">{row.value}</span>
                        <ExternalLink className="h-3 w-3 shrink-0" />
                      </a>
                    ) : (
                      <span className="break-words">{row.value}</span>
                    )}
                  </dd>
                </div>
              ))}
              {profile?.professional_summary && (
                <div className="flex items-start gap-2 text-sm md:col-span-2">
                  <dt className="text-muted-foreground shrink-0 min-w-36">Summary</dt>
                  <dd className="whitespace-pre-wrap">{profile.professional_summary}</dd>
                </div>
              )}
            </dl>
          )}
        </CardContent>
      </Card>

      <SkillsCard />

      {sections.map(config => (
        <SectionCard key={config.key} config={config} />
      ))}
    </div>
  )
}
