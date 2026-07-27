import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { TimelineAnalytics as TA } from '@/services/analytics'

interface TimelineAnalyticsProps {
  data: TA | null
  loading: boolean
}

function MiniBarChart({ data, color }: { data: { label: string; count: number }[]; color: string }) {
  const max = Math.max(...data.map(d => d.count), 1)
  return (
    <div className="flex items-end gap-0.5 h-24">
      {data.slice(-20).map((d, i) => (
        <div key={i} className="flex-1 flex flex-col items-center gap-0.5 group relative">
          <div className="absolute bottom-full mb-1 hidden group-hover:block bg-dark-700 text-xs px-1.5 py-0.5 rounded whitespace-nowrap z-10">
            {d.label}: {d.count}
          </div>
          <div
            className={cn('w-full rounded-t transition-all duration-300', color)}
            style={{ height: `${(d.count / max) * 100}%` }}
          />
        </div>
      ))}
    </div>
  )
}

export function TimelineAnalytics({ data, loading }: TimelineAnalyticsProps) {
  if (loading || !data) {
    return <Card><CardContent className="p-6"><div className="h-48 bg-dark-700 rounded animate-pulse" /></CardContent></Card>
  }

  const totalApps = data.applicationsPerWeek.reduce((a, b) => a + b.count, 0)
  const peakWeek = data.applicationsPerWeek.reduce((a, b) => a.count > b.count ? a : b, { week: '', count: 0 })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Timeline Activity
          <Badge variant="outline" className="text-xs">{totalApps} total</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-medium">Applications Per Week</h4>
            {peakWeek.count > 0 && (
              <span className="text-xs text-muted-foreground">Peak: {peakWeek.week} ({peakWeek.count})</span>
            )}
          </div>
          <MiniBarChart
            data={data.applicationsPerWeek.map(w => ({ label: w.week, count: w.count }))}
            color="bg-primary/50 hover:bg-primary/70"
          />
        </div>

        <div>
          <h4 className="text-sm font-medium mb-2">Monthly Activity</h4>
          <MiniBarChart
            data={data.monthlyActivity.map(m => ({ label: m.month, count: m.count }))}
            color="bg-purple-500/50 hover:bg-purple-500/70"
          />
        </div>

        {data.dailyActivity.length > 0 && (
          <div className="border-t border-glass-border pt-4">
            <h4 className="text-sm font-medium mb-2">Activity Summary</h4>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-semibold">{data.dailyActivity.length}</p>
                <p className="text-xs text-muted-foreground">Active days</p>
              </div>
              <div>
                <p className="text-2xl font-semibold">
                  {data.dailyActivity.length > 0
                    ? Math.round(totalApps / data.dailyActivity.length)
                    : 0}
                </p>
                <p className="text-xs text-muted-foreground">Avg apps/day</p>
              </div>
              <div>
                <p className="text-2xl font-semibold">
                  {data.monthlyActivity.length > 0
                    ? Math.round(totalApps / data.monthlyActivity.length)
                    : 0}
                </p>
                <p className="text-xs text-muted-foreground">Avg apps/month</p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
