import { useCallback, useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { jobsApi } from '../api/client'

interface JobPosting {
  id: string
  title: string
  company_name: string
  company_url: string | null
  company_logo_url: string | null
  location: string | null
  description: string | null
  url: string | null
  source: string
  source_job_id: string | null
  salary_min: number | null
  salary_max: number | null
  salary_currency: string | null
  salary_period: string | null
  posted_at: string | null
  job_type: string | null
  remote: boolean
  apply_url: string | null
  skills: string[]
  requirements: string[]
  benefits: string[]
  categories: string[]
  is_active: boolean
  viewed_at: string | null
  applied_at: string | null
  created_at: string
  updated_at: string
}

export function JobDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [job, setJob] = useState<JobPosting | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadJob = useCallback(async () => {
    if (!id) return
    setLoading(true)
    try {
      const data = await jobsApi.get(id)
      setJob(data)
    } catch (e: any) {
      setError(e.message || 'Failed to load job')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    loadJob()
  }, [loadJob])

  const handleMarkApplied = async () => {
    if (!id) return
    try {
      await jobsApi.markApplied(id)
      loadJob()
    } catch (e: any) {
      setError(e.message || 'Failed to mark as applied')
    }
  }

  const handleToggleActive = async () => {
    if (!id || !job) return
    try {
      await jobsApi.update(id, { is_active: !job.is_active })
      loadJob()
    } catch (e: any) {
      setError(e.message || 'Failed to update job')
    }
  }

  if (loading) return <div>Loading job details...</div>
  if (error) return <p style={{ color: 'red' }}>{error}</p>
  if (!job) return <p>Job not found.</p>

  const formatSalary = () => {
    if (job.salary_min == null && job.salary_max == null) return null
    const cur = job.salary_currency || 'USD'
    const per = job.salary_period ? `/${job.salary_period}` : ''
    if (job.salary_min != null && job.salary_max != null) return `${cur} ${job.salary_min.toLocaleString()} - ${job.salary_max.toLocaleString()}${per}`
    if (job.salary_min != null) return `${cur} ${job.salary_min.toLocaleString()}+${per}`
    return `${cur} ${job.salary_max!.toLocaleString()} max${per}`
  }

  return (
    <div>
      <Link to="/jobs">← Back to search</Link>
      <h1>{job.title}</h1>
      <p><strong>Company:</strong> {job.company_name}</p>
      <p><strong>Location:</strong> {job.remote ? 'Remote' : job.location || 'Not specified'}</p>
      <p><strong>Job Type:</strong> {job.job_type || 'Not specified'}</p>
      <p><strong>Source:</strong> {job.source}</p>
      {job.posted_at && <p><strong>Posted:</strong> {new Date(job.posted_at).toLocaleDateString()}</p>}
      {formatSalary() && <p><strong>Salary:</strong> {formatSalary()}</p>}
      {job.url && <p><strong>URL:</strong> <a href={job.url} target="_blank" rel="noopener noreferrer">{job.url}</a></p>}
      {job.apply_url && <p><strong>Apply:</strong> <a href={job.apply_url} target="_blank" rel="noopener noreferrer">{job.apply_url}</a></p>}

      <div style={{ display: 'flex', gap: 8, margin: '12px 0' }}>
        <button onClick={handleMarkApplied} disabled={!!job.applied_at}>
          {job.applied_at ? 'Applied' : 'Mark as Applied'}
        </button>
        <button onClick={handleToggleActive}>
          {job.is_active ? 'Deactivate' : 'Activate'}
        </button>
      </div>

      {job.description && (
        <section>
          <h2>Description</h2>
          <div dangerouslySetInnerHTML={{ __html: job.description }} />
        </section>
      )}

      {job.skills.length > 0 && (
        <section>
          <h2>Skills</h2>
          <ul>{job.skills.map((s, i) => <li key={i}>{s}</li>)}</ul>
        </section>
      )}

      {job.requirements.length > 0 && (
        <section>
          <h2>Requirements</h2>
          <ul>{job.requirements.map((r, i) => <li key={i}>{r}</li>)}</ul>
        </section>
      )}

      {job.benefits.length > 0 && (
        <section>
          <h2>Benefits</h2>
          <ul>{job.benefits.map((b, i) => <li key={i}>{b}</li>)}</ul>
        </section>
      )}

      {job.categories.length > 0 && (
        <section>
          <h2>Categories</h2>
          <p>{job.categories.join(', ')}</p>
        </section>
      )}
    </div>
  )
}
