import { useCallback, useState } from 'react'
import { Link } from 'react-router-dom'
import { jobsApi, matchingApi } from '../api/client'
import { ScoreBadge } from '../components/ScoreBadge'

interface JobPosting {
  id: string
  title: string
  company_name: string
  location: string | null
  salary_min: number | null
  salary_max: number | null
  salary_currency: string | null
  salary_period: string | null
  posted_at: string | null
  job_type: string | null
  remote: boolean
  source: string
  skills: string[]
  is_active: boolean
}

interface JobScore {
  [jobId: string]: number
}

export function JobSearchPage() {
  const [query, setQuery] = useState('')
  const [location, setLocation] = useState('')
  const [remoteOnly, setRemoteOnly] = useState(false)
  const [jobType, setJobType] = useState('')
  const [salaryMin, setSalaryMin] = useState('')
  const [salaryMax, setSalaryMax] = useState('')
  const [results, setResults] = useState<JobPosting[]>([])
  const [scores, setScores] = useState<JobScore>({})
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const doSearch = useCallback(async (pageNum = 1) => {
    if (!query.trim()) return
    setLoading(true)
    setError('')
    try {
      const res = await jobsApi.search({
        query: query.trim(),
        page: pageNum,
        page_size: 20,
        location: location.trim() || null,
        remote_only: remoteOnly || undefined,
        job_type: jobType || undefined,
        salary_min: salaryMin ? Number(salaryMin) : undefined,
        salary_max: salaryMax ? Number(salaryMax) : undefined,
      })
      setResults(res.items)
      setTotal(res.total)
      setPage(res.page)
      setTotalPages(res.total_pages)
      if (res.items.length > 0) {
        try {
          const batch = await matchingApi.scoreBatch({ job_ids: res.items.map((j: any) => j.id) })
          const m: JobScore = {}
          for (const s of batch.scores) {
            if (s.job_id) m[s.job_id] = s.overall
          }
          setScores(m)
        } catch {
          // scoring unavailable
        }
      }
    } catch (e: any) {
      setError(e.message || 'Search failed')
    } finally {
      setLoading(false)
    }
  }, [query, location, remoteOnly, jobType, salaryMin, salaryMax])

  const doRefresh = async () => {
    if (!query.trim()) return
    setLoading(true)
    setError('')
    try {
      const res = await jobsApi.refresh({ query: query.trim() })
      const poll = setInterval(async () => {
        try {
          const status = await jobsApi.taskStatus(res.task_id)
          if (status.status === 'completed') {
            clearInterval(poll)
            doSearch(1)
          } else if (status.status === 'failed') {
            clearInterval(poll)
            setError(status.error || 'Refresh failed')
            setLoading(false)
          }
        } catch {
          clearInterval(poll)
          setError('Status check failed')
          setLoading(false)
        }
      }, 2000)
    } catch (e: any) {
      setError(e.message || 'Refresh failed')
      setLoading(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
    doRefresh()
  }

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

  const sortByScore = () => {
    const sorted = [...results].sort((a, b) => {
      const sa = scores[a.id] ?? 0
      const sb = scores[b.id] ?? 0
      return sb - sa
    })
    setResults(sorted)
  }

  return (
    <div>
      <h1>Search Jobs</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <input
            placeholder="Job title, skills, or keywords"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{ width: 300 }}
          />
          <input
            placeholder="Location"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            style={{ width: 200 }}
          />
          <label>
            <input type="checkbox" checked={remoteOnly} onChange={(e) => setRemoteOnly(e.target.checked)} />
            Remote only
          </label>
          <select value={jobType} onChange={(e) => setJobType(e.target.value)}>
            <option value="">All types</option>
            <option value="full-time">Full-time</option>
            <option value="part-time">Part-time</option>
            <option value="contract">Contract</option>
            <option value="internship">Internship</option>
            <option value="temporary">Temporary</option>
          </select>
          <input
            placeholder="Salary min"
            type="number"
            value={salaryMin}
            onChange={(e) => setSalaryMin(e.target.value)}
            style={{ width: 100 }}
          />
          <input
            placeholder="Salary max"
            type="number"
            value={salaryMax}
            onChange={(e) => setSalaryMax(e.target.value)}
            style={{ width: 100 }}
          />
          <button type="submit" disabled={loading || !query.trim()}>
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {!loading && results.length > 0 && (
        <div>
          <p>{total} jobs found. Page {page} of {totalPages}</p>
          <div style={{ display: 'flex', gap: 4, marginBottom: 8 }}>
            {page > 1 && <button onClick={() => doSearch(page - 1)}>Previous</button>}
            {page < totalPages && <button onClick={() => doSearch(page + 1)}>Next</button>}
            <button onClick={() => doRefresh()} disabled={loading}>Refresh Results</button>
            {Object.keys(scores).length > 0 && <button onClick={sortByScore}>Sort by Match</button>}
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th>Match</th>
                <th>Title</th>
                <th>Company</th>
                <th>Location</th>
                <th>Salary</th>
                <th>Type</th>
                <th>Source</th>
                <th>Posted</th>
              </tr>
            </thead>
            <tbody>
              {results.map((job) => (
                <tr key={job.id}>
                  <td>
                    {scores[job.id] != null ? (
                      <ScoreBadge score={scores[job.id]} size="sm" />
                    ) : (
                      <span style={{ color: '#9ca3af', fontSize: 12 }}>-</span>
                    )}
                  </td>
                  <td><Link to={`/jobs/${job.id}`}>{job.title}</Link></td>
                  <td>{job.company_name}</td>
                  <td>{job.remote ? 'Remote' : job.location || '-'}</td>
                  <td>{formatSalary(job) || '-'}</td>
                  <td>{job.job_type || '-'}</td>
                  <td>{job.source}</td>
                  <td>{timeAgo(job.posted_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ display: 'flex', gap: 4, marginTop: 8 }}>
            {page > 1 && <button onClick={() => doSearch(page - 1)}>Previous</button>}
            {page < totalPages && <button onClick={() => doSearch(page + 1)}>Next</button>}
          </div>
        </div>
      )}

      {!loading && results.length === 0 && query && !error && (
        <p>No jobs found. Try a different search.</p>
      )}
    </div>
  )
}
