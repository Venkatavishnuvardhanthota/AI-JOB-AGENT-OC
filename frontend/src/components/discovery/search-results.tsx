import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Building2, MapPin, Clock, DollarSign, ExternalLink, Briefcase } from 'lucide-react'
import type { Job } from '@/services/discovery'

interface SearchResultsProps {
  jobs: Job[]
  totalFound: number
  duplicatesRemoved: number
  executionTime: number
  isLoading: boolean
}

function formatSalary(min: number | null, max: number | null, currency: string | null): string {
  if (min === null && max === null) return 'Not specified'
  const fmt = (n: number) => {
    if (!currency || currency === 'USD') return `$${n.toLocaleString()}`
    if (currency === 'INR') return `\u20B9${n.toLocaleString()}`
    return `${currency} ${n.toLocaleString()}`
  }
  if (min !== null && max !== null) return `${fmt(min)} - ${fmt(max)}`
  if (min !== null) return `From ${fmt(min)}`
  return `Up to ${fmt(max!)}`
}

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return 'Unknown'
  const diff = Date.now() - new Date(dateStr).getTime()
  const days = Math.floor(diff / 86400000)
  if (days === 0) return 'Today'
  if (days === 1) return 'Yesterday'
  if (days < 7) return `${days} days ago`
  if (days < 30) return `${Math.floor(days / 7)} weeks ago`
  if (days < 365) return `${Math.floor(days / 30)} months ago`
  return `${Math.floor(days / 365)} years ago`
}

export function SearchResults({ jobs, totalFound, duplicatesRemoved, executionTime, isLoading }: SearchResultsProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle className="text-lg">Results</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="animate-pulse">
                <div className="h-4 bg-dark-700 rounded w-3/4 mb-2" />
                <div className="h-3 bg-dark-700 rounded w-1/2 mb-2" />
                <div className="h-3 bg-dark-700 rounded w-1/3" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (jobs.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle className="text-lg">Results</CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No jobs found. Try adjusting your search criteria.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Results</CardTitle>
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span>{totalFound} found</span>
            <span>{duplicatesRemoved} duplicates</span>
            <span>{(executionTime / 1000).toFixed(1)}s</span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3 max-h-[600px] overflow-y-auto">
          {jobs.map(job => (
            <div key={job.id} className="p-3 rounded-lg border border-glass-border hover:bg-dark-800 transition-colors">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium truncate">{job.title}</h3>
                  <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1"><Building2 className="w-3 h-3" />{job.company}</span>
                    <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{job.location}</span>
                  </div>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  {job.easyApply && <Badge variant="secondary" className="text-[10px]">Easy Apply</Badge>}
                  <Badge variant="outline" className="text-[10px] capitalize">{job.remote}</Badge>
                </div>
              </div>
              <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                {job.salaryMin !== null && (
                  <span className="flex items-center gap-1"><DollarSign className="w-3 h-3" />{formatSalary(job.salaryMin, job.salaryMax, job.currency)}</span>
                )}
                {job.employmentType && (
                  <span className="flex items-center gap-1"><Briefcase className="w-3 h-3" />{job.employmentType.replace(/_/g, ' ')}</span>
                )}
                <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{timeAgo(job.postedDate)}</span>
              </div>
              <p className="text-xs text-muted-foreground mt-2 line-clamp-2">{job.description}</p>
              {job.requiredSkills.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {job.requiredSkills.slice(0, 5).map(skill => (
                    <Badge key={skill} variant="secondary" className="text-[10px]">{skill}</Badge>
                  ))}
                  {job.requiredSkills.length > 5 && (
                    <Badge variant="outline" className="text-[10px]">+{job.requiredSkills.length - 5}</Badge>
                  )}
                </div>
              )}
              <div className="flex items-center justify-between mt-2 pt-2 border-t border-glass-border">
                <span className="text-[10px] text-muted-foreground capitalize">{job.provider}</span>
                <Button variant="ghost" size="sm" className="h-6 text-xs" asChild>
                  <a href={job.sourceUrl} target="_blank" rel="noopener noreferrer">
                    View <ExternalLink className="w-3 h-3 ml-1" />
                  </a>
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
