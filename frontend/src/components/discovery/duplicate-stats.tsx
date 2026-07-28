import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { BarChart3, Copy, Percent } from 'lucide-react'

interface DuplicateStatsProps {
  totalJobs: number
  uniqueJobs: number
  duplicatesRemoved: number
}

export function DuplicateStats({ totalJobs, uniqueJobs, duplicatesRemoved }: DuplicateStatsProps) {
  if (totalJobs === 0) return null

  const duplicateRate = totalJobs > 0 ? Math.round((duplicatesRemoved / totalJobs) * 100) : 0

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <BarChart3 className="w-5 h-5" />
          Duplicate Analysis
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-2xl font-bold">{totalJobs}</div>
            <p className="text-xs text-muted-foreground flex items-center justify-center gap-1 mt-1">
              <Copy className="w-3 h-3" /> Total Results
            </p>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-2xl font-bold text-green-400">{uniqueJobs}</div>
            <p className="text-xs text-muted-foreground flex items-center justify-center gap-1 mt-1">
              <BarChart3 className="w-3 h-3" /> Unique Jobs
            </p>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-2xl font-bold text-yellow-400">{duplicateRate}%</div>
            <p className="text-xs text-muted-foreground flex items-center justify-center gap-1 mt-1">
              <Percent className="w-3 h-3" /> Duplicate Rate
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
