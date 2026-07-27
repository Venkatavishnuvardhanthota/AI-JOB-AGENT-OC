import { useQuery } from '@tanstack/react-query'
import { applicationService } from '@/services/application'
import { StatCard } from '@/components/layout/stat-card'
import { Skeleton } from '@/components/ui/skeleton'
import { FileText, Send, CalendarCheck, Briefcase, Target, TrendingUp } from 'lucide-react'

export function ApplicationStatsCards() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['applications', 'stats'],
    queryFn: () => applicationService.getStats(),
  })

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-24 rounded-xl" />
        ))}
      </div>
    )
  }

  if (!stats) return null

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      <StatCard
        icon={FileText}
        title="Total Applications"
        value={stats.total}
      />
      <StatCard
        icon={Send}
        title="Applied This Week"
        value={stats.applied_this_week}
      />
      <StatCard
        icon={CalendarCheck}
        title="Interviews"
        value={stats.interviews}
      />
      <StatCard
        icon={Briefcase}
        title="Offers"
        value={stats.offers}
      />
      <StatCard
        icon={Target}
        title="Acceptance Rate"
        value={`${Math.round(stats.acceptance_rate * 100)}%`}
      />
      <StatCard
        icon={TrendingUp}
        title="Response Rate"
        value={`${Math.round(stats.response_rate * 100)}%`}
      />
    </div>
  )
}
