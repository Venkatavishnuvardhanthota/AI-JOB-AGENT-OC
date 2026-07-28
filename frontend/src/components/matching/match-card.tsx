import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Building2, MapPin, DollarSign, Clock, Briefcase } from 'lucide-react'
import { ScoreBadge } from '@/components/ScoreBadge'
import { getDecisionLabel, getDecisionColor } from '@/services/matching'
import type { MatchResult } from '@/services/matching'

interface MatchCardProps {
  match: MatchResult
  rank?: number
}

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return 'Unknown'
  const diff = Date.now() - new Date(dateStr).getTime()
  const days = Math.floor(diff / 86400000)
  if (days === 0) return 'Today'
  if (days === 1) return 'Yesterday'
  return `${days} days ago`
}

export function MatchCard({ match, rank }: MatchCardProps) {
  const { job } = match

  return (
    <Card className="hover:border-primary/30 transition-colors">
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          <div className="flex flex-col items-center gap-1 shrink-0 w-16">
            <ScoreBadge score={match.overall} size="md" />
            <span className="text-[10px] text-muted-foreground">{Math.round(match.confidence * 100)}% conf</span>
          </div>

          {rank && (
            <div className="flex items-center justify-center w-6 h-6 rounded-full bg-dark-700 text-xs font-bold shrink-0 mt-1">
              {rank}
            </div>
          )}

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h3 className="text-sm font-medium truncate">{job.title}</h3>
                <div className="flex items-center gap-2 mt-0.5 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1"><Building2 className="w-3 h-3" />{job.company}</span>
                  <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{job.location}</span>
                </div>
              </div>
              <Badge className={`text-[10px] shrink-0 ${getDecisionColor(match.decision)}`}>
                {getDecisionLabel(match.decision)}
              </Badge>
            </div>

            <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
              {job.salaryMin !== null && (
                <span className="flex items-center gap-1"><DollarSign className="w-3 h-3" />{formatSalary(job.salaryMin, job.salaryMax, job.currency)}</span>
              )}
              <span className="flex items-center gap-1"><Briefcase className="w-3 h-3" />{job.employmentType.replace(/_/g, ' ')}</span>
              <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{timeAgo(job.postedDate)}</span>
            </div>

            <div className="flex items-center gap-3 mt-2">
              <div className="flex-1 h-1.5 bg-dark-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 rounded-full"
                  style={{ width: `${match.overall * 100}%` }}
                />
              </div>
              <span className="text-xs font-medium">{Math.round(match.overall * 100)}%</span>
            </div>

            <div className="flex items-center gap-2 mt-2">
              {job.requiredSkills.slice(0, 4).map(s => (
                <Badge key={s} variant="secondary" className="text-[10px]">{s}</Badge>
              ))}
              {job.requiredSkills.length > 4 && (
                <Badge variant="outline" className="text-[10px]">+{job.requiredSkills.length - 4}</Badge>
              )}
            </div>

            <div className="flex items-center gap-2 mt-2 text-[10px] text-muted-foreground">
              <span className="capitalize">{job.provider}</span>
              <span>{match.skillDetail.matchedCount}/{match.skillDetail.totalJobSkills} skills</span>
              {match.missingSkills.length > 0 && (
                <span className="text-yellow-400">{match.missingSkills.length} missing</span>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
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
