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

  const loadProfile = useCallback(async () => {
    try {
      const [p, ed, ex, pr, sk, ce, la, bl] = await Promise.all([
        api.get<UserProfile>('/profile'),
        api.get<Education[]>('/profile/education'),
        api.get<Experience[]>('/profile/experience'),
        api.get<Project[]>('/profile/projects'),
        api.get<Skill[]>('/profile/skills'),
        api.get<Certification[]>('/profile/certifications'),
        api.get<Language[]>('/profile/languages'),
        api.get<BlacklistedCompany[]>('/profile/blacklist'),
      ])
      setProfile(p)
      setEducations(ed)
      setExperiences(ex)
      setProjects(pr)
      setSkills(sk)
      setCertifications(ce)
      setLanguages(la)
      setBlacklist(bl)
    } catch {
      // handle error
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadProfile()
  }, [loadProfile])

  if (loading) return <div>Loading profile...</div>

  return (
    <div>
      <h1>My Profile</h1>
      <p>Welcome, {user?.full_name || user?.email}</p>

      <section>
        <h2>Personal Details</h2>
        <ProfileForm profile={profile} onUpdate={loadProfile} />
      </section>

      <section>
        <h2>Education</h2>
        <EntityList
          items={educations}
          renderItem={(e) => `${e.degree} at ${e.institution}`}
          emptyText="No education added yet."
        />
      </section>

      <section>
        <h2>Experience</h2>
        <EntityList
          items={experiences}
          renderItem={(e) => `${e.title} at ${e.company}`}
          emptyText="No experience added yet."
        />
      </section>

      <section>
        <h2>Projects</h2>
        <EntityList
          items={projects}
          renderItem={(p) => p.name}
          emptyText="No projects added yet."
        />
      </section>

      <section>
        <h2>Skills</h2>
        <EntityList
          items={skills}
          renderItem={(s) => `${s.name} (${s.proficiency || 'N/A'})`}
          emptyText="No skills added yet."
        />
      </section>

      <section>
        <h2>Certifications</h2>
        <EntityList
          items={certifications}
          renderItem={(c) => c.name}
          emptyText="No certifications added yet."
        />
      </section>

      <section>
        <h2>Languages</h2>
        <EntityList
          items={languages}
          renderItem={(l) => `${l.name} - ${l.proficiency}`}
          emptyText="No languages added yet."
        />
      </section>

      <section>
        <h2>Blacklisted Companies</h2>
        <EntityList
          items={blacklist}
          renderItem={(b) => b.company_name}
          emptyText="No companies blacklisted."
        />
      </section>
    </div>
  )
}

function ProfileForm({
  profile,
  onUpdate,
}: {
  profile: UserProfile | null
  onUpdate: () => void
}) {
  const [form, setForm] = useState({
    phone: profile?.phone || '',
    headline: profile?.headline || '',
    bio: profile?.bio || '',
    location: profile?.location || '',
    salary_expectation_min: profile?.salary_expectation_min || '',
    salary_expectation_max: profile?.salary_expectation_max || '',
    salary_currency: profile?.salary_currency || '',
    linkedin_url: profile?.linkedin_url || '',
    github_url: profile?.github_url || '',
    portfolio_url: profile?.portfolio_url || '',
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const payload: Record<string, unknown> = {}
    for (const [key, value] of Object.entries(form)) {
      if (value !== '') {
        payload[key] = key.includes('salary') ? Number(value) : value
      }
    }
    await api.put('/profile', payload)
    onUpdate()
  }

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      await api.uploadFile('/profile/resume', file)
      onUpdate()
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label>Headline</label>
        <input name="headline" value={form.headline} onChange={handleChange} />
      </div>
      <div>
        <label>Phone</label>
        <input name="phone" value={form.phone} onChange={handleChange} />
      </div>
      <div>
        <label>Location</label>
        <input name="location" value={form.location} onChange={handleChange} />
      </div>
      <div>
        <label>Bio</label>
        <textarea name="bio" value={form.bio} onChange={handleChange} />
      </div>
      <div>
        <label>Salary Min</label>
        <input name="salary_expectation_min" type="number" value={form.salary_expectation_min} onChange={handleChange} />
      </div>
      <div>
        <label>Salary Max</label>
        <input name="salary_expectation_max" type="number" value={form.salary_expectation_max} onChange={handleChange} />
      </div>
      <div>
        <label>Currency</label>
        <input name="salary_currency" value={form.salary_currency} onChange={handleChange} maxLength={3} />
      </div>
      <div>
        <label>LinkedIn URL</label>
        <input name="linkedin_url" value={form.linkedin_url} onChange={handleChange} />
      </div>
      <div>
        <label>GitHub URL</label>
        <input name="github_url" value={form.github_url} onChange={handleChange} />
      </div>
      <div>
        <label>Portfolio URL</label>
        <input name="portfolio_url" value={form.portfolio_url} onChange={handleChange} />
      </div>
      <div>
        <label>Resume</label>
        <input type="file" accept=".pdf,.doc,.docx" onChange={handleResumeUpload} />
        {profile?.resume_file && <p>Resume uploaded</p>}
      </div>
      <button type="submit">Save Profile</button>
    </form>
  )
}

function EntityList<T extends { id: string }>({
  items,
  renderItem,
  emptyText,
}: {
  items: T[]
  renderItem: (item: T) => string
  emptyText: string
}) {
  if (items.length === 0) return <p>{emptyText}</p>
  return (
    <ul>
      {items.map((item) => (
        <li key={item.id}>{renderItem(item)}</li>
      ))}
    </ul>
  )
}
