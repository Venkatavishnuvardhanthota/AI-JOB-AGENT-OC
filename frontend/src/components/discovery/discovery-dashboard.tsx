import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Search, Copy, Clock, Activity, TrendingUp } from 'lucide-react'
import type { DiscoveryStatistics } from '@/services/discovery'

interface DiscoveryDashboardProps {
  statistics: DiscoveryStatistics
}

export function DiscoveryDashboard({ statistics }: DiscoveryDashboardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Activity className="w-5 h-5" />
          Discovery Overview
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="text-center p-3 rounded-lg bg-dark-800">
            <div className="flex items-center justify-center text-2xl font-bold">{statistics.totalSearches}</div>
            <p className="text-xs text-muted-foreground flex items-center justify-center gap-1 mt-1">
              <Search className="w-3 h-3" /> Searches
            </p>
          </div>
          <div className="text-center p-3 rounded-lg bg-dark-800">
            <div className="flex items-center justify-center text-2xl font-bold text-blue-400">{statistics.totalJobsDiscovered}</div>
            <p className="text-xs text-muted-foreground flex items-center justify-center gap-1 mt-1">
              <Copy className="w-3 h-3" /> Jobs Found
            </p>
          </div>
          <div className="text-center p-3 rounded-lg bg-dark-800">
            <div className="flex items-center justify-center text-2xl font-bold text-green-400">{statistics.totalDuplicatesRemoved}</div>
            <p className="text-xs text-muted-foreground flex items-center justify-center gap-1 mt-1">
              <Copy className="w-3 h-3" /> Duplicates
            </p>
          </div>
          <div className="text-center p-3 rounded-lg bg-dark-800">
            <div className="flex items-center justify-center text-2xl font-bold">{(statistics.averageExecutionTime / 1000).toFixed(1)}s</div>
            <p className="text-xs text-muted-foreground flex items-center justify-center gap-1 mt-1">
              <Clock className="w-3 h-3" /> Avg Time
            </p>
          </div>
          <div className="text-center p-3 rounded-lg bg-dark-800">
            <div className="flex items-center justify-center text-2xl font-bold text-yellow-400">{statistics.searchesToday}</div>
            <p className="text-xs text-muted-foreground flex items-center justify-center gap-1 mt-1">
              <TrendingUp className="w-3 h-3" /> Today
            </p>
          </div>
          <div className="text-center p-3 rounded-lg bg-dark-800">
            <div className="flex items-center justify-center text-2xl font-bold text-purple-400">{statistics.searchesThisWeek}</div>
            <p className="text-xs text-muted-foreground flex items-center justify-center gap-1 mt-1">
              <Activity className="w-3 h-3" /> This Week
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
