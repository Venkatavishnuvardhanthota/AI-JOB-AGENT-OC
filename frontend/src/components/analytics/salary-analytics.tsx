import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { SalaryAnalytics as SA } from '@/services/analytics'
import { TrendingUp } from 'lucide-react'

interface SalaryAnalyticsProps {
  data: SA | null
  loading: boolean
}

export function SalaryAnalytics({ data, loading }: SalaryAnalyticsProps) {
  if (loading || !data) {
    return <Card><CardContent className="p-6"><div className="h-40 bg-dark-700 rounded animate-pulse" /></CardContent></Card>
  }

  const fmt = (n: number) => n > 0 ? `$${(n / 1000).toFixed(0)}k` : 'N/A'
  const maxVal = Math.max(data.expected.avg, data.offered.avg, data.accepted.avg, 1)

  const bars = [
    { label: 'Expected', value: data.expected.avg, color: 'bg-blue-500/40' },
    { label: 'Offered', value: data.offered.avg, color: 'bg-amber-500/40' },
    { label: 'Accepted', value: data.accepted.avg, color: 'bg-green-500/40' },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Salary Analytics
          {(data.offered.avg > data.expected.avg) && (
            <Badge variant="default" className="text-xs flex items-center gap-1">
              <TrendingUp className="h-3 w-3" /> Offers above expected
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {bars.map(bar => (
            <div key={bar.label}>
              <div className="flex items-center justify-between text-sm mb-1">
                <span>{bar.label}</span>
                <span className="font-medium">{fmt(bar.value)}</span>
              </div>
              <div className="h-6 rounded bg-dark-700 overflow-hidden">
                <div
                  className={cn('h-full rounded transition-all duration-500', bar.color)}
                  style={{ width: `${(bar.value / maxVal) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>

        {data.byLocation.length > 0 && (
          <div className="mt-4 pt-4 border-t border-glass-border">
            <h4 className="text-sm font-medium mb-2">By Location</h4>
            <div className="grid grid-cols-2 gap-2">
              {data.byLocation.map(loc => (
                <div key={loc.location} className="flex items-center justify-between text-xs bg-dark-800 rounded px-2 py-1">
                  <span className="truncate">{loc.location}</span>
                  <span className="font-medium ml-2">{fmt(loc.avg)} ({loc.count})</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
