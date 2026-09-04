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
  education: { institution: '', degree: '', field_of_study: '', location: '', cgpa: '', start_date: '', end_date: '', currently_studying: false },
  experience: { company: '', title: '', location: '', employment_type: '', start_date: '', end_date: '', currently_working: false, responsibilities: '', achievements: '', technologies_used: '', description: '' },
  projects: { name: '', description: '', technologies: '', github_url: '', demo_url: '', live_url: '', start_date: '', end_date: '' },
  skills: { name: '', category: '', proficiency: '', years_experience: '', skill_level: '' },
  certifications: { name: '', issuer: '', credential_id: '', credential_url: '', issue_date: '', expiration_date: '' },
  languages: { language: '', proficiency: 'Beginner' },
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
        if (Array.isArray(value)) {
          if (value.length > 0) payload[key] = value
        } else if (typeof value === 'boolean' || (value !== '' && value !== null)) {
          payload[key] = key === 'years_experience' ? Number(value) : value
        }
      }
      if (item?.id) {
        await api.patch(`/profile/${section}/${item.id}`, payload)
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
            {renderField('location', 'Location')}
            {renderField('cgpa', 'CGPA')}
            <div className="form-row">
              {renderField('start_date', 'Start Date', 'date')}
              {renderField('end_date', 'End Date', 'date')}
            </div>
            {renderField('currently_studying', 'I currently study here', 'checkbox')}
          </>
        )
      case 'experience':
        return (
          <>
            {renderField('company', 'Company')}
            {renderField('title', 'Title')}
            {renderField('location', 'Location')}
            {renderField('employment_type', 'Employment Type', 'select', ['Full-time', 'Part-time', 'Contract', 'Freelance', 'Internship'])}
            <div className="form-row">
              {renderField('start_date', 'Start Date', 'date')}
              {renderField('end_date', 'End Date', 'date')}
            </div>
            {renderField('currently_working', 'I currently work here', 'checkbox')}
            {renderField('responsibilities', 'Responsibilities (one per line)', 'textarea')}
            {renderField('achievements', 'Key Achievements (one per line)', 'textarea')}
            {renderField('technologies_used', 'Technologies (one per line)', 'textarea')}
          </>
        )
      case 'projects':
        return (
          <>
            {renderField('name', 'Project Name')}
            {renderField('description', 'Description', 'textarea')}
            {renderField('technologies', 'Technologies (one per line)', 'textarea')}
            {renderField('github_url', 'GitHub URL')}
            {renderField('demo_url', 'Demo URL')}
            {renderField('live_url', 'Live URL')}
            <div className="form-row">
              {renderField('start_date', 'Start Date', 'date')}
              {renderField('end_date', 'End Date', 'date')}
            </div>
          </>
        )
      case 'skills':
        return (
          <>
            {renderField('name', 'Skill Name')}
            {renderField('category', 'Category')}
            {renderField('proficiency', 'Proficiency', 'select', ['Beginner', 'Intermediate', 'Advanced', 'Expert'])}
            {renderField('years_experience', 'Years of Experience', 'number')}
            {renderField('skill_level', 'Skill Level', 'select', ['Learning', 'Comfortable', 'Proficient', 'Expert'])}
          </>
        )
      case 'certifications':
        return (
          <>
            {renderField('name', 'Certification Name')}
            {renderField('issuer', 'Issuer')}
            <div className="form-row">
              {renderField('issue_date', 'Issue Date', 'date')}
              {renderField('expiration_date', 'Expiration Date', 'date')}
            </div>
            {renderField('credential_id', 'Credential ID')}
            {renderField('credential_url', 'Credential URL')}
          </>
        )
      case 'languages':
        return (
          <>
            {renderField('language', 'Language')}
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
    headline: profile?.headline || '',
    current_role: profile?.current_role || '',
    desired_role: profile?.desired_role || '',
    employment_status: profile?.employment_status || '',
    total_years_experience: profile?.total_years_experience ?? '',
    notice_period: profile?.notice_period || '',
    current_salary: profile?.current_salary ?? '',
    expected_salary: profile?.expected_salary ?? '',
    salary_preference: profile?.salary_preference || '',
    willing_to_relocate: !!profile?.willing_to_relocate,
    visa_sponsorship_requirement: !!profile?.visa_sponsorship_requirement,
    linkedin_url: profile?.linkedin_url || '',
    github_url: profile?.github_url || '',
    portfolio_url: profile?.portfolio_url || '',
    website_url: profile?.website_url || '',
    professional_summary: profile?.professional_summary || '',
  })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (profile) {
      setForm({
        headline: profile.headline || '',
        current_role: profile.current_role || '',
        desired_role: profile.desired_role || '',
        employment_status: profile.employment_status || '',
        total_years_experience: profile.total_years_experience ?? '',
        notice_period: profile.notice_period || '',
        current_salary: profile.current_salary ?? '',
        expected_salary: profile.expected_salary ?? '',
        salary_preference: profile.salary_preference || '',
        willing_to_relocate: !!profile.willing_to_relocate,
        visa_sponsorship_requirement: !!profile.visa_sponsorship_requirement,
        linkedin_url: profile.linkedin_url || '',
        github_url: profile.github_url || '',
        portfolio_url: profile.portfolio_url || '',
        website_url: profile.website_url || '',
        professional_summary: profile.professional_summary || '',
      })
    }
  }, [profile])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const target = e.target
    const value = target.type === 'checkbox' ? (target as HTMLInputElement).checked : target.value
    setForm(prev => ({ ...prev, [target.name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    const payload: Record<string, unknown> = {}
    for (const [key, value] of Object.entries(form)) {
      if (typeof value === 'boolean' || value !== '') payload[key] = value
    }
    try {
      await api.patch('/profile', payload)
      onToast('Profile saved successfully!', 'success')
      onUpdate()
    } catch (err: any) {
      onToast(err.message || 'Failed to save profile', 'error')
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
          <label>Current Role</label>
          <input name="current_role" value={form.current_role} onChange={handleChange} placeholder="e.g. Software Engineer" />
        </div>
      </div>
      <div className="form-row">
        <div className="form-group">
          <label>Desired Role</label>
          <input name="desired_role" value={form.desired_role} onChange={handleChange} placeholder="e.g. Senior Backend Engineer" />
        </div>
        <div className="form-group">
          <label>Employment Status</label>
          <select name="employment_status" value={form.employment_status} onChange={handleChange}>
            <option value="">Select...</option>
            <option value="employed">Employed</option>
            <option value="self_employed">Self-employed</option>
            <option value="freelancer">Freelancer</option>
            <option value="student">Student</option>
            <option value="unemployed">Unemployed</option>
            <option value="retired">Retired</option>
          </select>
        </div>
      </div>
      <div className="form-group">
        <label>Professional Summary</label>
        <textarea name="professional_summary" value={form.professional_summary} onChange={handleChange} placeholder="Tell us about yourself..." />
      </div>
      <div className="form-row">
        <div className="form-group">
          <label>Total Years of Experience</label>
          <input name="total_years_experience" type="number" step="0.5" value={form.total_years_experience} onChange={handleChange} />
        </div>
        <div className="form-group">
          <label>Notice Period</label>
          <input name="notice_period" value={form.notice_period} onChange={handleChange} placeholder="e.g. 30 days" />
        </div>
      </div>
      <div className="form-row">
        <div className="form-group">
          <label>Current Salary</label>
          <input name="current_salary" type="number" value={form.current_salary} onChange={handleChange} />
        </div>
        <div className="form-group">
          <label>Expected Salary</label>
          <input name="expected_salary" type="number" value={form.expected_salary} onChange={handleChange} placeholder="e.g. 90000" />
        </div>
      </div>
      <div className="form-group">
        <label>Salary Preference</label>
        <select name="salary_preference" value={form.salary_preference} onChange={handleChange}>
          <option value="">Select...</option>
          <option value="paid_only">Paid only</option>
          <option value="paid_preferred">Paid preferred, unpaid considered</option>
          <option value="unpaid_acceptable">Open to unpaid</option>
        </select>
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
      <div className="form-row">
        <div className="form-group">
          <label>Portfolio URL</label>
          <input name="portfolio_url" value={form.portfolio_url} onChange={handleChange} placeholder="https://..." />
        </div>
        <div className="form-group">
          <label>Website URL</label>
          <input name="website_url" value={form.website_url} onChange={handleChange} placeholder="https://..." />
        </div>
      </div>
      <div className="form-group">
        <label className="checkbox-label">
          <input type="checkbox" name="willing_to_relocate" checked={form.willing_to_relocate} onChange={handleChange} />
          Willing to relocate
        </label>
      </div>
      <div className="form-group">
        <label className="checkbox-label">
          <input type="checkbox" name="visa_sponsorship_requirement" checked={form.visa_sponsorship_requirement} onChange={handleChange} />
          Requires visa sponsorship
        </label>
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
        return { title: `${item.title} at ${item.company}`, subtitle: item.currently_working ? 'Current' : '' }
      case 'projects':
        return { title: item.name, subtitle: item.description ? item.description : '' }
      case 'skills':
        return { title: item.name, subtitle: item.proficiency ? `Proficiency: ${item.proficiency}` : '' }
      case 'certifications':
        return { title: item.name, subtitle: item.issuer || '' }
      case 'languages':
        return { title: `${item.language} - ${item.proficiency}`, subtitle: '' }
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
