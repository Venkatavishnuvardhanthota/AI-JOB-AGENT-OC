import { Card, CardContent } from '@/components/ui/card'
import { StatCard } from '@/components/layout/stat-card'
import type { ApplicationStats } from '@/types'
import { Briefcase, Calendar, BarChart3, TrendingUp, Target, Activity } from 'lucide-react'

interface OverviewCardsProps {
  stats: ApplicationStats | null | undefined
  loading: boolean
}

export function AnalyticsOverviewCards({ stats, loading }: OverviewCardsProps) {
  if (loading || !stats) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {[1, 2, 3, 4, 5, 6].map(i => (
          <Card key={i}><CardContent className="p-4"><div className="h-20 bg-dark-700 rounded animate-pulse" /></CardContent></Card>
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      <StatCard title="Total Applications" value={stats.total} icon={Briefcase} />
      <StatCard title="Applied This Week" value={stats.applied_this_week} icon={Calendar} />
      <StatCard title="Interviews" value={stats.interviews} icon={BarChart3} />
      <StatCard title="Offers" value={stats.offers} icon={Target} />
      <StatCard title="Acceptance Rate" value={`${Math.round(stats.acceptance_rate * 100)}%`} icon={TrendingUp} />
      <StatCard title="Response Rate" value={`${Math.round(stats.response_rate * 100)}%`} icon={Activity} />
    </div>
  )
}
