import { useState, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select } from '@/components/ui/select'
import { computeCohortAnalytics } from '@/services/timeline-intelligence'
import { cn } from '@/lib/utils'
import type { Application } from '@/types'
import { TrendingUp, TrendingDown, Minus, BarChart3 } from 'lucide-react'

interface CohortAnalyticsProps {
  applications: Application[]
  loading: boolean
}

export function CohortAnalytics({ applications, loading }: CohortAnalyticsProps) {
  const [period, setPeriod] = useState<'weekly' | 'monthly' | 'quarterly'>('monthly')

  const cohorts = useMemo(() => computeCohortAnalytics(applications, period), [applications, period])

  if (loading) {
    return <Card><CardContent className="p-6"><div className="h-48 bg-dark-700 rounded animate-pulse" /></CardContent></Card>
  }

  if (cohorts.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <BarChart3 className="h-4 w-4 text-primary" /> Cohort Analytics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-6">Not enough data to compare periods.</p>
        </CardContent>
      </Card>
    )
  }

  // Calculate trend arrows between consecutive cohorts
  const trends = cohorts.slice(1).map((curr, i) => {
    const prev = cohorts[i]
    return {
      interviewTrend: curr.interviewRate > prev.interviewRate ? 'up' : curr.interviewRate < prev.interviewRate ? 'down' : 'flat',
      offerTrend: curr.offerRate > prev.offerRate ? 'up' : curr.offerRate < prev.offerRate ? 'down' : 'flat',
    }
  })

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm">
            <BarChart3 className="h-4 w-4 text-primary" /> Cohort Analytics
            <Badge variant="outline" className="text-[10px]">{cohorts.length} periods</Badge>
          </CardTitle>
          <Select value={period} onChange={(e) => setPeriod(e.target.value as any)} className="w-24 h-7 text-xs" aria-label="Period">
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
            <option value="quarterly">Quarterly</option>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-glass-border">
                <th className="text-left py-2 pr-3 font-medium">Period</th>
                <th className="text-right px-2 py-2 font-medium">Apps</th>
                <th className="text-right px-2 py-2 font-medium">Int</th>
                <th className="text-right px-2 py-2 font-medium">Int %</th>
                <th className="text-right px-2 py-2 font-medium">Offers</th>
                <th className="text-right px-2 py-2 font-medium">Off %</th>
                <th className="text-right px-2 py-2 font-medium">Acc %</th>
              </tr>
            </thead>
            <tbody>
              {cohorts.map((cohort, i) => {
                const trend = i > 0 ? trends[i - 1] : null
                return (
                  <tr key={cohort.label} className="border-b border-glass-border/50 hover:bg-dark-800/50 transition-colors">
                    <td className="py-2 pr-3 font-medium">{cohort.label}</td>
                    <td className="text-right px-2 py-2 tabular-nums">{cohort.applications}</td>
                    <td className="text-right px-2 py-2 tabular-nums">{cohort.interviews}</td>
                    <td className="text-right px-2 py-2">
                      <div className="flex items-center justify-end gap-1">
                        <span className="tabular-nums">{cohort.interviewRate}%</span>
                        {trend && (
                          trend.interviewTrend === 'up' ? <TrendingUp className="h-3 w-3 text-green-400" /> :
                          trend.interviewTrend === 'down' ? <TrendingDown className="h-3 w-3 text-red-400" /> :
                          <Minus className="h-3 w-3 text-muted-foreground" />
                        )}
                      </div>
                    </td>
                    <td className="text-right px-2 py-2 tabular-nums">{cohort.offers}</td>
                    <td className="text-right px-2 py-2">
                      <div className="flex items-center justify-end gap-1">
                        <span className="tabular-nums">{cohort.offerRate}%</span>
                        {trend && (
                          trend.offerTrend === 'up' ? <TrendingUp className="h-3 w-3 text-green-400" /> :
                          trend.offerTrend === 'down' ? <TrendingDown className="h-3 w-3 text-red-400" /> :
                          <Minus className="h-3 w-3 text-muted-foreground" />
                        )}
                      </div>
                    </td>
                    <td className="text-right px-2 py-2 tabular-nums">{cohort.acceptanceRate}%</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        <div className="mt-4 space-y-1">
          {cohorts.length >= 2 && (
            <>
              {(() => {
                const first = cohorts[0]
                const last = cohorts[cohorts.length - 1]
                const intDiff = last.interviewRate - first.interviewRate
                const offDiff = last.offerRate - first.offerRate

                return (
                  <div className="space-y-1">
                    {intDiff !== 0 && (
                      <p className={cn(
                        'text-xs flex items-center gap-1',
                        intDiff > 0 ? 'text-green-400' : 'text-red-400',
                      )}>
                        {intDiff > 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                        Interview rate {intDiff > 0 ? 'improved' : 'declined'} by {Math.abs(intDiff)}% from {first.label} to {last.label}
                      </p>
                    )}
                    {offDiff !== 0 && (
                      <p className={cn(
                        'text-xs flex items-center gap-1',
                        offDiff > 0 ? 'text-green-400' : 'text-red-400',
                      )}>
                        {offDiff > 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                        Offer rate {offDiff > 0 ? 'improved' : 'declined'} by {Math.abs(offDiff)}% from {first.label} to {last.label}
                      </p>
                    )}
                  </div>
                )
              })()}
            </>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
