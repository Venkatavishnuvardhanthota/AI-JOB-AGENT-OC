import { useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useJobSearch, useRefreshJobs, useScoreBatch } from '@/api/hooks'
import { PageHeader } from '@/components/layout/page-header'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Search, RefreshCw, Briefcase, MapPin, DollarSign, Clock } from 'lucide-react'
import { timeAgo, formatSalary, getScoreBg } from '@/lib/utils'

export function JobsSearchPage() {
  const [query, setQuery] = useState('')
  const [searchParams, setSearchParams] = useState<Record<string, any> | null>(null)
  const [page, setPage] = useState(1)
  const [scores, setScores] = useState<Record<string, number>>({})

  const { data, isLoading } = useJobSearch((searchParams || { query: '', page: 1 }) as any)
  const refreshJobs = useRefreshJobs()
  const scoreBatch = useScoreBatch()

  const results = (data as any)?.items || []
  const total = (data as any)?.total || 0
  const totalPages = (data as any)?.total_pages || 1

  const doSearch = useCallback(async (pageNum = 1) => {
    if (!query.trim()) return
    const params = { query: query.trim(), page: pageNum, page_size: 20 }
    setSearchParams(params)
    setPage(pageNum)
  }, [query])

  const handleRefresh = async () => {
    if (!query.trim()) return
    try {
      await refreshJobs.mutateAsync({ query: query.trim() })
      doSearch(1)
    } catch {}
  }

  const handleScoreBatch = async () => {
    if (results.length === 0) return
    try {
      const res = await scoreBatch.mutateAsync({ job_ids: results.map((j: any) => j.id) }) as any
      const m: Record<string, number> = {}
      for (const s of (res.scores || [])) {
        if (s.job_id) m[s.job_id] = s.overall
      }
      setScores(m)
    } catch {}
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
    doSearch(1)
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Search Jobs" description="Find your next opportunity." />

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Job title, skills, or keywords"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          <Button type="submit" disabled={!query.trim() || isLoading}>
            {isLoading ? 'Searching...' : 'Search'}
          </Button>
          <Button type="button" variant="outline" onClick={handleRefresh} disabled={!query.trim()}>
            <RefreshCw className="h-4 w-4 mr-1" /> Refresh
          </Button>
        </div>
      </form>

      {isLoading && (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}
        </div>
      )}

      {!isLoading && results.length > 0 && (
        <>
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">{total} jobs found. Page {page} of {totalPages}</p>
            <Button variant="outline" size="sm" onClick={handleScoreBatch} disabled={scoreBatch.isPending}>
              Score Matches
            </Button>
          </div>
          <div className="space-y-3">
            {results.map((job: any) => (
              <Link key={job.id} to={`/jobs/${job.id}`}>
                <Card className="hover:bg-white/[0.03] transition-colors">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="space-y-1 flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-foreground">{job.title}</h3>
                          {scores[job.id] != null && (
                            <span className={`text-xs px-1.5 py-0.5 rounded ${getScoreBg(scores[job.id])}`}>
                              {Math.round(scores[job.id])}%
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground">{job.company_name}</p>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{job.remote ? 'Remote' : job.location || '-'}</span>
                          <span className="flex items-center gap-1"><DollarSign className="h-3 w-3" />{formatSalary(job.salary_min, job.salary_max, job.salary_currency, job.salary_period)}</span>
                          <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{timeAgo(job.posted_at)}</span>
                        </div>
                      </div>
                      <div className="flex items-start gap-2">
                        <Badge variant="secondary" className="text-xs">{job.source}</Badge>
                        {job.job_type && <Badge variant="outline" className="text-xs">{job.job_type}</Badge>}
                      </div>
                    </div>
                    {job.skills && job.skills.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {job.skills.slice(0, 5).map((skill: string) => (
                          <Badge key={skill} variant="secondary" className="text-xs">{skill}</Badge>
                        ))}
                        {job.skills.length > 5 && <span className="text-xs text-muted-foreground">+{job.skills.length - 5} more</span>}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
          {totalPages > 1 && (
            <div className="flex justify-center gap-2">
              <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => doSearch(page - 1)}>Previous</Button>
              <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => doSearch(page + 1)}>Next</Button>
            </div>
          )}
        </>
      )}

      {!isLoading && results.length === 0 && searchParams?.query && (
        <div className="text-center py-16 text-muted-foreground">
          <Briefcase className="h-12 w-12 mx-auto mb-4 opacity-30" />
          <p>No jobs found. Try a different search.</p>
        </div>
      )}
    </div>
  )
}
