import { useState, useEffect } from 'react'
import { useProfile, useUpdateProfile, useProfileSection, useCreateProfileSection, useUpdateProfileSection, useDeleteProfileSection, useProfileCompleteness } from '@/api/hooks'
import { PageHeader } from '@/components/layout/page-header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { useToast } from '@/components/ui/toast'
import { UserCircle, Plus, Pencil, Trash2, GraduationCap, Briefcase, Wrench, FolderGit2, Award, Languages, Link as LinkIcon } from 'lucide-react'

const sections = [
  { key: 'education', label: 'Education', icon: GraduationCap },
  { key: 'experience', label: 'Experience', icon: Briefcase },
  { key: 'skills', label: 'Skills', icon: Wrench },
  { key: 'projects', label: 'Projects', icon: FolderGit2 },
  { key: 'certifications', label: 'Certifications', icon: Award },
  { key: 'languages', label: 'Languages', icon: Languages },
  { key: 'social-links', label: 'Social Links', icon: LinkIcon },
] as const

export function CareerProfilePage() {
  const { data: profile, isLoading: profileLoading } = useProfile() as any
  const { data: completeness } = useProfileCompleteness()
  const updateProfile = useUpdateProfile()
  const { addToast } = useToast()

  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({
    headline: '', bio: '', location: '', phone: '',
    salary_expectation_min: '', linkedin_url: '', github_url: '', portfolio_url: '',
  })

  useEffect(() => {
    if (profile) {
      setForm({
        headline: profile.headline || '',
        bio: profile.bio || '',
        location: profile.location || '',
        phone: profile.phone || '',
        salary_expectation_min: profile.salary_expectation_min?.toString() || '',
        linkedin_url: profile.linkedin_url || '',
        github_url: profile.github_url || '',
        portfolio_url: profile.portfolio_url || '',
      })
    }
  }, [profile])

  const handleSaveProfile = async () => {
    try {
      const payload: Record<string, any> = {}
      for (const [k, v] of Object.entries(form)) {
        if (v !== '') payload[k] = k === 'salary_expectation_min' ? Number(v) : v
      }
      await updateProfile.mutateAsync(payload)
      addToast('Profile updated!', 'success')
      setEditing(false)
    } catch { addToast('Failed to update profile', 'error') }
  }

  if (profileLoading) return <div className="space-y-4">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}</div>

  return (
    <div className="space-y-6 max-w-4xl">
      <PageHeader
        title="Career Profile"
        description={completeness ? `Profile ${Math.round((completeness as any).score)}% complete` : 'Manage your career details'}
        actions={
          <Button variant={editing ? 'default' : 'outline'} onClick={() => editing ? handleSaveProfile() : setEditing(true)} disabled={updateProfile.isPending}>
            {editing ? 'Save' : 'Edit'}
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UserCircle className="h-5 w-5 text-primary" />
            Personal Details
          </CardTitle>
        </CardHeader>
        <CardContent>
          {editing ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-muted-foreground block mb-1">Headline</label>
                <Input value={form.headline} onChange={e => setForm(f => ({ ...f, headline: e.target.value }))} placeholder="e.g. Senior Software Engineer" />
              </div>
              <div>
                <label className="text-xs text-muted-foreground block mb-1">Phone</label>
                <Input value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} placeholder="+1 (555) 123-4567" />
              </div>
              <div>
                <label className="text-xs text-muted-foreground block mb-1">Location</label>
                <Input value={form.location} onChange={e => setForm(f => ({ ...f, location: e.target.value }))} placeholder="e.g. San Francisco, CA" />
              </div>
              <div>
                <label className="text-xs text-muted-foreground block mb-1">Salary Expectation (Min)</label>
                <Input type="number" value={form.salary_expectation_min} onChange={e => setForm(f => ({ ...f, salary_expectation_min: e.target.value }))} placeholder="80000" />
              </div>
              <div>
                <label className="text-xs text-muted-foreground block mb-1">LinkedIn URL</label>
                <Input value={form.linkedin_url} onChange={e => setForm(f => ({ ...f, linkedin_url: e.target.value }))} placeholder="https://linkedin.com/in/..." />
              </div>
              <div>
                <label className="text-xs text-muted-foreground block mb-1">GitHub URL</label>
                <Input value={form.github_url} onChange={e => setForm(f => ({ ...f, github_url: e.target.value }))} placeholder="https://github.com/..." />
              </div>
              <div>
                <label className="text-xs text-muted-foreground block mb-1">Portfolio URL</label>
                <Input value={form.portfolio_url} onChange={e => setForm(f => ({ ...f, portfolio_url: e.target.value }))} placeholder="https://..." />
              </div>
              <div className="md:col-span-2">
                <label className="text-xs text-muted-foreground block mb-1">Bio</label>
                <textarea className="w-full rounded-md border border-glass-border bg-dark-900 px-3 py-2 text-sm text-foreground min-h-[80px]" value={form.bio} onChange={e => setForm(f => ({ ...f, bio: e.target.value }))} placeholder="Tell us about yourself..." />
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {[
                { label: 'Headline', value: profile?.headline },
                { label: 'Phone', value: profile?.phone },
                { label: 'Location', value: profile?.location },
                { label: 'Salary Expectation', value: profile?.salary_expectation_min ? `$${profile.salary_expectation_min.toLocaleString()}+` : null },
                { label: 'LinkedIn', value: profile?.linkedin_url },
                { label: 'GitHub', value: profile?.github_url },
                { label: 'Portfolio', value: profile?.portfolio_url },
              ].filter(x => x.value).map(item => (
                <div key={item.label} className="flex items-start gap-2 text-sm">
                  <span className="text-muted-foreground min-w-28">{item.label}:</span>
                  <span>{item.value}</span>
                </div>
              ))}
              {profile?.bio && <div className="text-sm mt-2"><span className="text-muted-foreground">Bio:</span><p className="mt-1 whitespace-pre-wrap">{profile.bio}</p></div>}
              {!profile?.headline && !profile?.bio && !profile?.location && (
                <p className="text-sm text-muted-foreground">No details added yet. Click Edit to add your information.</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {sections.map(section => (
        <SectionCard key={section.key} section={section.key} label={section.label} icon={section.icon} />
      ))}
    </div>
  )
}

function SectionCard({ section, label, icon: Icon }: { section: string; label: string; icon: any }) {
  const [showForm, setShowForm] = useState(false)
  const [editingItem, setEditingItem] = useState<any | null>(null)
  const [form, setForm] = useState<Record<string, string>>({})
  const { data: items, isLoading } = useProfileSection<any>(section)
  const createItem = useCreateProfileSection(section)
  const updateItem = useUpdateProfileSection(section)
  const deleteItem = useDeleteProfileSection(section)
  const { addToast } = useToast()

  const handleSave = async () => {
    const payload: Record<string, any> = {}
    for (const [k, v] of Object.entries(form)) {
      if (v !== '') payload[k] = k === 'proficiency' || k === 'gpa' ? Number(v) : v
    }
    try {
      if (editingItem) {
        await updateItem.mutateAsync({ id: editingItem.id, data: payload })
        addToast(`${label} updated!`, 'success')
      } else {
        await createItem.mutateAsync(payload)
        addToast(`${label} added!`, 'success')
      }
      setShowForm(false)
      setEditingItem(null)
      setForm({})
    } catch { addToast('Failed to save', 'error') }
  }

  const handleEdit = (item: any) => {
    setEditingItem(item)
    setForm(item)
    setShowForm(true)
  }

  const handleDelete = async (id: string) => {
    try { await deleteItem.mutateAsync(id); addToast(`${label} deleted`, 'info') }
    catch { addToast('Failed to delete', 'error') }
  }

  const fields = getFields(section)

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Icon className="h-5 w-5 text-primary" />
            {label}
          </CardTitle>
          <Button variant="outline" size="sm" onClick={() => { setShowForm(true); setEditingItem(null); setForm({}) }}>
            <Plus className="h-4 w-4 mr-1" /> Add
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-16 w-full" />
        ) : !items || items.length === 0 ? (
          <p className="text-sm text-muted-foreground">No {label.toLowerCase()} added yet.</p>
        ) : (
          <div className="space-y-2">
            {items.map((item: any) => (
              <div key={item.id} className="flex items-center justify-between p-3 rounded-lg bg-dark-800/30 hover:bg-dark-800/50">
                <div>
                  <p className="text-sm font-medium">{item.name || item.institution || item.company || item.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {item.degree && `${item.degree} · `}
                    {item.issuer && `${item.issuer} · `}
                    {item.proficiency && `Level: ${item.proficiency} · `}
                    {item.category && `${item.category} · `}
                    {item.company && `${item.company} · `}
                    {item.field_of_study && `${item.field_of_study}`}
                  </p>
                </div>
                <div className="flex gap-1">
                  <Button variant="ghost" size="sm" onClick={() => handleEdit(item)}><Pencil className="h-4 w-4" /></Button>
                  <Button variant="ghost" size="sm" onClick={() => handleDelete(item.id)}><Trash2 className="h-4 w-4 text-error" /></Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>

      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => { setShowForm(false); setEditingItem(null) }}>
          <div className="bg-dark-900 border border-glass-border rounded-xl p-6 w-96 max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">{editingItem ? 'Edit' : 'Add'} {label}</h3>
            <div className="space-y-3">
              {fields.map(f => (
                <div key={f.key}>
                  <label className="text-xs text-muted-foreground block mb-1">{f.label}</label>
                  {f.type === 'textarea' ? (
                    <textarea className="w-full rounded-md border border-glass-border bg-dark-800 px-3 py-2 text-sm text-foreground min-h-[60px]" value={form[f.key] || ''} onChange={e => setForm(p => ({ ...p, [f.key]: e.target.value }))} />
                  ) : f.type === 'select' && f.options ? (
                    <select className="w-full rounded-md border border-glass-border bg-dark-800 px-3 py-2 text-sm text-foreground" value={form[f.key] || ''} onChange={e => setForm(p => ({ ...p, [f.key]: e.target.value }))}>
                      <option value="">Select...</option>
                      {f.options.map(o => <option key={o} value={o}>{o}</option>)}
                    </select>
                  ) : (
                    <Input type={f.type || 'text'} value={form[f.key] || ''} onChange={e => setForm(p => ({ ...p, [f.key]: e.target.value }))} />
                  )}
                </div>
              ))}
            </div>
            <div className="flex justify-end gap-2 mt-4">
              <Button variant="outline" onClick={() => { setShowForm(false); setEditingItem(null) }}>Cancel</Button>
              <Button onClick={handleSave} disabled={createItem.isPending || updateItem.isPending}>{editingItem ? 'Update' : 'Add'}</Button>
            </div>
          </div>
        </div>
      )}
    </Card>
  )
}

function getFields(section: string): { key: string; label: string; type?: string; options?: string[] }[] {
  const common: Record<string, any> = {
    education: [
      { key: 'institution', label: 'Institution' },
      { key: 'degree', label: 'Degree' },
      { key: 'field_of_study', label: 'Field of Study' },
      { key: 'start_date', label: 'Start Date', type: 'date' },
      { key: 'end_date', label: 'End Date', type: 'date' },
      { key: 'gpa', label: 'GPA', type: 'number' },
      { key: 'description', label: 'Description', type: 'textarea' },
    ],
    experience: [
      { key: 'company', label: 'Company' },
      { key: 'title', label: 'Title' },
      { key: 'location', label: 'Location' },
      { key: 'start_date', label: 'Start Date', type: 'date' },
      { key: 'end_date', label: 'End Date', type: 'date' },
      { key: 'description', label: 'Description', type: 'textarea' },
      { key: 'company_url', label: 'Company URL' },
    ],
    skills: [
      { key: 'name', label: 'Skill Name' },
      { key: 'category', label: 'Category' },
      { key: 'proficiency', label: 'Proficiency (1-100)', type: 'number' },
    ],
    projects: [
      { key: 'name', label: 'Project Name' },
      { key: 'description', label: 'Description', type: 'textarea' },
      { key: 'url', label: 'URL' },
      { key: 'github_url', label: 'GitHub URL' },
      { key: 'start_date', label: 'Start Date', type: 'date' },
      { key: 'end_date', label: 'End Date', type: 'date' },
    ],
    certifications: [
      { key: 'name', label: 'Certification Name' },
      { key: 'issuer', label: 'Issuer' },
      { key: 'issue_date', label: 'Issue Date', type: 'date' },
      { key: 'expiry_date', label: 'Expiry Date', type: 'date' },
      { key: 'credential_id', label: 'Credential ID' },
      { key: 'credential_url', label: 'Credential URL' },
    ],
    languages: [
      { key: 'name', label: 'Language' },
      { key: 'proficiency', label: 'Proficiency', type: 'select', options: ['Beginner', 'Intermediate', 'Advanced', 'Fluent', 'Native'] },
    ],
    'social-links': [
      { key: 'platform', label: 'Platform' },
      { key: 'url', label: 'URL' },
    ],
  }
  return common[section] || []
}
