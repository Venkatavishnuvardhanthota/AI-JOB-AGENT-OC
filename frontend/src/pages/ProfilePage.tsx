import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import type {
  BlacklistedCompany,
  Certification,
  Education,
  Experience,
  Language,
  Project,
  Skill,
  UserProfile,
} from '../types'
import '../styles/ProfilePage.css'

interface Toast {
  id: number
  message: string
  type: 'success' | 'error'
}

let toastId = 0
const sections = [
  { key: 'education', label: 'Education', icon: '🎓', empty: 'No education added yet.' },
  { key: 'experience', label: 'Experience', icon: '💼', empty: 'No experience added yet.' },
  { key: 'projects', label: 'Projects', icon: '🚀', empty: 'No projects added yet.' },
  { key: 'skills', label: 'Skills', icon: '⚡', empty: 'No skills added yet.' },
  { key: 'certifications', label: 'Certifications', icon: '🏅', empty: 'No certifications added yet.' },
  { key: 'languages', label: 'Languages', icon: '🌐', empty: 'No languages added yet.' },
  { key: 'blacklist', label: 'Blacklisted Companies', icon: '🚫', empty: 'No companies blacklisted.' },
] as const

type SectionKey = typeof sections[number]['key']

interface ModalState {
  section: SectionKey
  item: Record<string, any> | null
}

const defaultForms: Record<SectionKey, Record<string, any>> = {
  education: { institution: '', degree: '', field_of_study: '', start_date: '', end_date: '', gpa: '', description: '' },
  experience: { company: '', title: '', location: '', start_date: '', end_date: '', is_current: false, description: '', company_url: '' },
  projects: { name: '', description: '', url: '', github_url: '', start_date: '', end_date: '', is_current: false },
  skills: { name: '', category: '', proficiency: '' },
  certifications: { name: '', issuer: '', issue_date: '', expiry_date: '', credential_id: '', credential_url: '' },
  languages: { name: '', proficiency: 'Beginner' },
  blacklist: { company_name: '', reason: '' },
}

function EntityModal({ section, item, onClose, onSaved }: {
  section: SectionKey
  item: Record<string, any> | null
  onClose: () => void
  onSaved: () => void
}) {
  const defaults = defaultForms[section]
  const [form, setForm] = useState<Record<string, any>>(item ? { ...defaults, ...item } : { ...defaults })
  const [saving, setSaving] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const target = e.target
    const value = target.type === 'checkbox' ? (target as HTMLInputElement).checked : target.value
    setForm(prev => ({ ...prev, [target.name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      const payload: Record<string, any> = {}
      for (const [key, value] of Object.entries(form)) {
        if (value !== '' && value !== null) {
          payload[key] = key === 'gpa' || key === 'proficiency' ? Number(value) : value
        }
      }
      if (item?.id) {
        await api.put(`/profile/${section}/${item.id}`, payload)
      } else {
        await api.post(`/profile/${section}`, payload)
      }
      onSaved()
      onClose()
    } catch (err: any) {
      alert(err.message || 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  const renderField = (key: string, label: string, type: string = 'text', options?: string[]) => {
    if (type === 'checkbox') {
      return (
        <div className="form-group" key={key}>
          <label className="checkbox-label">
            <input type="checkbox" name={key} checked={!!form[key]} onChange={handleChange} />
            {label}
          </label>
        </div>
      )
    }
    if (type === 'select' && options) {
      return (
        <div className="form-group" key={key}>
          <label>{label}</label>
          <select name={key} value={form[key] || ''} onChange={handleChange}>
            <option value="">Select...</option>
            {options.map(o => <option key={o} value={o}>{o}</option>)}
          </select>
        </div>
      )
    }
    return (
      <div className="form-group" key={key}>
        <label>{label}</label>
        {type === 'textarea' ? (
          <textarea name={key} value={form[key] || ''} onChange={handleChange} />
        ) : (
          <input type={type} name={key} value={form[key] || ''} onChange={handleChange} />
        )}
      </div>
    )
  }

  const renderFields = () => {
    switch (section) {
      case 'education':
        return (
          <>
            {renderField('institution', 'Institution')}
            {renderField('degree', 'Degree')}
            {renderField('field_of_study', 'Field of Study')}
            <div className="form-row">
              {renderField('start_date', 'Start Date', 'date')}
              {renderField('end_date', 'End Date', 'date')}
            </div>
            <div className="form-row">
              {renderField('gpa', 'GPA', 'number')}
            </div>
            {renderField('description', 'Description', 'textarea')}
          </>
        )
      case 'experience':
        return (
          <>
            {renderField('company', 'Company')}
            {renderField('title', 'Title')}
            {renderField('location', 'Location')}
            <div className="form-row">
              {renderField('start_date', 'Start Date', 'date')}
              {renderField('end_date', 'End Date', 'date')}
            </div>
            {renderField('is_current', 'I currently work here', 'checkbox')}
            {renderField('description', 'Description', 'textarea')}
            {renderField('company_url', 'Company URL')}
          </>
        )
      case 'projects':
        return (
          <>
            {renderField('name', 'Project Name')}
            {renderField('description', 'Description', 'textarea')}
            {renderField('url', 'URL')}
            {renderField('github_url', 'GitHub URL')}
            <div className="form-row">
              {renderField('start_date', 'Start Date', 'date')}
              {renderField('end_date', 'End Date', 'date')}
            </div>
            {renderField('is_current', 'Ongoing', 'checkbox')}
          </>
        )
      case 'skills':
        return (
          <>
            {renderField('name', 'Skill Name')}
            {renderField('category', 'Category')}
            {renderField('proficiency', 'Proficiency (1-100)', 'number')}
          </>
        )
      case 'certifications':
        return (
          <>
            {renderField('name', 'Certification Name')}
            {renderField('issuer', 'Issuer')}
            <div className="form-row">
              {renderField('issue_date', 'Issue Date', 'date')}
              {renderField('expiry_date', 'Expiry Date', 'date')}
            </div>
            {renderField('credential_id', 'Credential ID')}
            {renderField('credential_url', 'Credential URL')}
          </>
        )
      case 'languages':
        return (
          <>
            {renderField('name', 'Language')}
            {renderField('proficiency', 'Proficiency', 'select', ['Beginner', 'Intermediate', 'Advanced', 'Fluent', 'Native'])}
          </>
        )
      case 'blacklist':
        return (
          <>
            {renderField('company_name', 'Company Name')}
            {renderField('reason', 'Reason', 'textarea')}
          </>
        )
    }
  }

  return (
    <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div className="modal">
        <h3>{item ? 'Edit' : 'Add'} {sections.find(s => s.key === section)?.label}</h3>
        <form onSubmit={handleSubmit}>
          {renderFields()}
          <div className="modal-actions">
            <button type="button" className="btn-cancel" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-save" disabled={saving}>
              {saving ? 'Saving...' : item ? 'Update' : 'Add'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function Toast({ toast, onClose }: { toast: Toast; onClose: (id: number) => void }) {
  useEffect(() => {
    const timer = setTimeout(() => onClose(toast.id), 3500)
    return () => clearTimeout(timer)
  }, [toast.id, onClose])

  return (
    <div className={`toast toast-${toast.type}`}>
      <span>{toast.type === 'success' ? '✓' : '✕'}</span>
      <span>{toast.message}</span>
      <button className="toast-close" onClick={() => onClose(toast.id)}>×</button>
    </div>
  )
}

function ProfileForm({ profile, onUpdate, onToast }: {
  profile: UserProfile | null
  onUpdate: () => void
  onToast: (msg: string, type: 'success' | 'error') => void
}) {
  const [form, setForm] = useState({
    phone: profile?.phone || '',
    headline: profile?.headline || '',
    bio: profile?.bio || '',
    location: profile?.location || '',
    salary_expectation_min: profile?.salary_expectation_min ?? '',
    linkedin_url: profile?.linkedin_url || '',
    github_url: profile?.github_url || '',
    portfolio_url: profile?.portfolio_url || '',
  })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (profile) {
      setForm({
        phone: profile.phone || '',
        headline: profile.headline || '',
        bio: profile.bio || '',
        location: profile.location || '',
        salary_expectation_min: profile.salary_expectation_min ?? '',
        linkedin_url: profile.linkedin_url || '',
        github_url: profile.github_url || '',
        portfolio_url: profile.portfolio_url || '',
      })
    }
  }, [profile])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    const payload: Record<string, unknown> = {}
    for (const [key, value] of Object.entries(form)) {
      if (value !== '') payload[key] = value
    }
    try {
      await api.put('/profile', payload)
      onToast('Profile saved successfully!', 'success')
      onUpdate()
    } catch (err: any) {
      onToast(err.message || 'Failed to save profile', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setSaving(true)
    try {
      await api.uploadFile('/profile/resume', file)
      onToast('Resume uploaded!', 'success')
      onUpdate()
    } catch (err: any) {
      onToast(err.message || 'Failed to upload resume', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-row">
        <div className="form-group">
          <label>Headline</label>
          <input name="headline" value={form.headline} onChange={handleChange} placeholder="e.g. Senior Software Engineer" />
        </div>
        <div className="form-group">
          <label>Phone</label>
          <input name="phone" value={form.phone} onChange={handleChange} placeholder="+1 (555) 123-4567" />
        </div>
      </div>
      <div className="form-group">
        <label>Location</label>
        <input name="location" value={form.location} onChange={handleChange} placeholder="e.g. San Francisco, CA" />
      </div>
      <div className="form-group">
        <label>Bio</label>
        <textarea name="bio" value={form.bio} onChange={handleChange} placeholder="Tell us about yourself..." />
      </div>
      <div className="form-group">
        <label>Salary Expectation (Min)</label>
        <input name="salary_expectation_min" type="number" value={form.salary_expectation_min} onChange={handleChange} placeholder="e.g. 80000" />
      </div>
      <div className="form-row">
        <div className="form-group">
          <label>LinkedIn URL</label>
          <input name="linkedin_url" value={form.linkedin_url} onChange={handleChange} placeholder="https://linkedin.com/in/..." />
        </div>
        <div className="form-group">
          <label>GitHub URL</label>
          <input name="github_url" value={form.github_url} onChange={handleChange} placeholder="https://github.com/..." />
        </div>
      </div>
      <div className="form-group">
        <label>Portfolio URL</label>
        <input name="portfolio_url" value={form.portfolio_url} onChange={handleChange} placeholder="https://..." />
      </div>
      <div className="form-group">
        <label>Resume</label>
        <input type="file" accept=".pdf,.doc,.docx" onChange={handleResumeUpload} />
        {profile?.resume_file && <p style={{ color: 'var(--success)', fontSize: '0.85rem', marginTop: '0.3rem' }}>✓ Resume uploaded</p>}
      </div>
      <button type="submit" className="add-btn" disabled={saving} style={{ marginTop: '0.5rem' }}>
        {saving ? 'Saving...' : 'Save Profile'}
      </button>
    </form>
  )
}

export function ProfilePage() {
  const { user } = useAuth()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [educations, setEducations] = useState<Education[]>([])
  const [experiences, setExperiences] = useState<Experience[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [skills, setSkills] = useState<Skill[]>([])
  const [certifications, setCertifications] = useState<Certification[]>([])
  const [languages, setLanguages] = useState<Language[]>([])
  const [blacklist, setBlacklist] = useState<BlacklistedCompany[]>([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState<ModalState | null>(null)
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = useCallback((message: string, type: 'success' | 'error') => {
    const id = ++toastId
    setToasts(prev => [...prev, { id, message, type }])
  }, [])

  const removeToast = useCallback((id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const allEntities: Record<SectionKey, any[]> = {
    education: educations,
    experience: experiences,
    projects,
    skills,
    certifications,
    languages,
    blacklist,
  }

  const loadProfile = useCallback(async () => {
    try {
      const [p, ed, ex, pr, sk, ce, la, bl] = await Promise.all([
        api.get<UserProfile>('/profile').catch(() => null),
        api.get<Education[]>('/profile/education').catch(() => []),
        api.get<Experience[]>('/profile/experience').catch(() => []),
        api.get<Project[]>('/profile/projects').catch(() => []),
        api.get<Skill[]>('/profile/skills').catch(() => []),
        api.get<Certification[]>('/profile/certifications').catch(() => []),
        api.get<Language[]>('/profile/languages').catch(() => []),
        api.get<BlacklistedCompany[]>('/profile/blacklist').catch(() => []),
      ])
      if (p) setProfile(p)
      if (ed) setEducations(ed)
      if (ex) setExperiences(ex)
      if (pr) setProjects(pr)
      if (sk) setSkills(sk)
      if (ce) setCertifications(ce)
      if (la) setLanguages(la)
      if (bl) setBlacklist(bl)
    } catch {
      // individual catch handlers prevent total failure
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadProfile() }, [loadProfile])

  const handleDelete = async (section: SectionKey, id: string) => {
    if (!confirm('Are you sure you want to delete this item?')) return
    try {
      await api.delete(`/profile/${section}/${id}`)
      addToast('Item deleted successfully!', 'success')
      loadProfile()
    } catch (err: any) {
      addToast(err.message || 'Failed to delete', 'error')
    }
  }

  const renderItemContent = (section: SectionKey, item: any) => {
    switch (section) {
      case 'education':
        return { title: `${item.degree} at ${item.institution}`, subtitle: item.field_of_study ? item.field_of_study : '' }
      case 'experience':
        return { title: `${item.title} at ${item.company}`, subtitle: item.is_current ? 'Current' : '' }
      case 'projects':
        return { title: item.name, subtitle: '' }
      case 'skills':
        return { title: item.name, subtitle: item.proficiency ? `Proficiency: ${item.proficiency}` : '' }
      case 'certifications':
        return { title: item.name, subtitle: item.issuer || '' }
      case 'languages':
        return { title: `${item.name} - ${item.proficiency}`, subtitle: '' }
      case 'blacklist':
        return { title: item.company_name, subtitle: item.reason || '' }
    }
  }

  if (loading) return (
    <div className="profile-page" style={{ textAlign: 'center', paddingTop: '4rem' }}>
      <div style={{ color: 'var(--text-muted)' }}>Loading profile...</div>
    </div>
  )

  return (
    <div className="profile-page">
      <div className="toast-container">
        {toasts.map(t => <Toast key={t.id} toast={t} onClose={removeToast} />)}
      </div>

      <div className="profile-header">
        <h1>My Profile</h1>
        <p>Welcome, {[user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.email}</p>
      </div>

      <div className="section-card">
        <div className="section-header">
          <h2><span className="icon">👤</span> Personal Details</h2>
        </div>
        <ProfileForm profile={profile} onUpdate={loadProfile} onToast={addToast} />
      </div>

      {sections.map(section => {
        const entities = allEntities[section.key]
        return (
          <div className="section-card" key={section.key}>
            <div className="section-header">
              <h2><span className="icon">{section.icon}</span> {section.label}</h2>
              <button className="add-btn" onClick={() => setModal({ section: section.key, item: null })}>+ Add</button>
            </div>
            {entities.length === 0 ? (
              <p className="empty-text">{section.empty}</p>
            ) : (
              <ul className="item-list">
                {entities.map((item: any) => {
                  const content = renderItemContent(section.key, item)
                  return (
                    <li className="item-card" key={item.id}>
                      <div className="item-card-content">
                        <div className="item-card-title">{content.title}</div>
                        {content.subtitle && <div className="item-card-subtitle">{content.subtitle}</div>}
                      </div>
                      <div className="item-card-actions">
                        <button className="edit-btn" onClick={() => setModal({ section: section.key, item })} title="Edit">✎</button>
                        <button className="delete-btn" onClick={() => handleDelete(section.key, item.id)} title="Delete">✕</button>
                      </div>
                    </li>
                  )
                })}
              </ul>
            )}
          </div>
        )
      })}

      {modal && (
        <EntityModal
          section={modal.section}
          item={modal.item}
          onClose={() => setModal(null)}
          onSaved={() => addToast(`${sections.find(s => s.key === modal.section)?.label} saved!`, 'success')}
        />
      )}
    </div>
  )
}
