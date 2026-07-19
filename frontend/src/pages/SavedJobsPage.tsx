import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { jobsApi } from '../api/client'

interface JobPosting {
  id: string
  title: string
  company_name: string
  location: string | null
  source: string
  job_type: string | null
  remote: boolean
  posted_at: string | null
  applied_at: string | null
  salary_min: number | null
  salary_max: number | null
  salary_currency: string | null
  salary_period: string | null
  is_active: boolean
}

export function SavedJobsPage() {
  const [jobs, setJobs] = useState<JobPosting[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadJobs = useCallback(async (pageNum = 1) => {
    setLoading(true)
    setError('')
    try {
      const res = await jobsApi.saved({ page: pageNum, page_size: 20 })
      setJobs(res.items)
      setTotal(res.total)
      setPage(res.page)
      setTotalPages(res.total_pages)
    } catch (e: any) {
      setError(e.message || 'Failed to load saved jobs')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadJobs(1)
  }, [loadJobs])

  const formatSalary = (j: JobPosting) => {
    if (j.salary_min == null && j.salary_max == null) return ''
    const cur = j.salary_currency || 'USD'
    const per = j.salary_period ? `/${j.salary_period}` : ''
    if (j.salary_min != null && j.salary_max != null) return `${cur} ${j.salary_min.toLocaleString()} - ${j.salary_max.toLocaleString()}${per}`
    if (j.salary_min != null) return `${cur} ${j.salary_min.toLocaleString()}+${per}`
    return `${cur} ${j.salary_max!.toLocaleString()} max${per}`
  }

  const timeAgo = (d: string | null) => {
    if (!d) return ''
    const diff = Date.now() - new Date(d).getTime()
    const days = Math.floor(diff / 86400000)
    if (days < 1) return 'Today'
    if (days === 1) return 'Yesterday'
    if (days < 30) return `${days}d ago`
    return `${Math.floor(days / 30)}mo ago`
  }

  if (loading) return <div>Loading saved jobs...</div>
  if (error) return <p style={{ color: 'red' }}>{error}</p>

  return (
    <div>
      <h1>Saved Jobs</h1>
      <p>{total} saved job{total !== 1 ? 's' : ''}</p>

      {jobs.length > 0 && (
        <div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th>Title</th>
                <th>Company</th>
                <th>Location</th>
                <th>Salary</th>
                <th>Type</th>
                <th>Source</th>
                <th>Status</th>
                <th>Posted</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id}>
                  <td><Link to={`/jobs/${job.id}`}>{job.title}</Link></td>
                  <td>{job.company_name}</td>
                  <td>{job.remote ? 'Remote' : job.location || '-'}</td>
                  <td>{formatSalary(job) || '-'}</td>
                  <td>{job.job_type || '-'}</td>
                  <td>{job.source}</td>
                  <td>
                    {job.applied_at ? 'Applied' : job.is_active ? 'Active' : 'Inactive'}
                  </td>
                  <td>{timeAgo(job.posted_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ display: 'flex', gap: 4, marginTop: 8 }}>
            {page > 1 && <button onClick={() => loadJobs(page - 1)}>Previous</button>}
            {page < totalPages && <button onClick={() => loadJobs(page + 1)}>Next</button>}
          </div>
        </div>
      )}

      {jobs.length === 0 && <p>No saved jobs yet. Search for jobs to save them.</p>}
    </div>
  )
}
