import { useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { computeHeatMap } from '@/services/timeline-intelligence'
import { cn } from '@/lib/utils'
import type { Application } from '@/types'
import { Calendar } from 'lucide-react'

interface HeatMapProps {
  applications: Application[]
  loading: boolean
}

export function HeatMap({ applications, loading }: HeatMapProps) {
  const heatMapData = useMemo(() => computeHeatMap(applications), [applications])

  if (loading) {
    return <Card><CardContent className="p-6"><div className="h-48 bg-dark-700 rounded animate-pulse" /></CardContent></Card>
  }

  const maxVal = heatMapData.maxValue || 1

  const getHeatColor = (value: number) => {
    const intensity = value / maxVal
    if (intensity === 0) return 'bg-dark-800'
    if (intensity < 0.25) return 'bg-primary/15'
    if (intensity < 0.5) return 'bg-primary/30'
    if (intensity < 0.75) return 'bg-primary/50'
    return 'bg-primary/70'
  }

  const totalApplications = heatMapData.data.flat().reduce((a, b) => a + b, 0)
  const maxDay = heatMapData.weekday[
    heatMapData.data.reduce((bestIdx, row, idx) =>
      row.reduce((a, b) => a + b, 0) > heatMapData.data[bestIdx].reduce((a, b) => a + b, 0) ? idx : bestIdx
    , 0)
  ]
  const peakHour = heatMapData.hourSlots[
    heatMapData.data[0].reduce((bestIdx, _, colIdx) => {
      const total = heatMapData.data.reduce((sum, row) => sum + row[colIdx], 0)
      const best = heatMapData.data.reduce((sum, row) => sum + row[bestIdx], 0)
      return total > best ? colIdx : bestIdx
    }, 0)
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm">
          <Calendar className="h-4 w-4 text-primary" /> Activity Heat Map
          <Badge variant="outline" className="text-[10px]">{totalApplications} activities</Badge>
        </CardTitle>
        {maxDay && (
          <p className="text-[10px] text-muted-foreground">Most active day: {maxDay} | Peak hour: {peakHour}</p>
        )}
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <div className="flex gap-1">
            <div className="flex flex-col gap-1 pr-2 pt-5">
              {heatMapData.weekday.map(d => (
                <div key={d} className="h-3 text-[9px] text-muted-foreground text-right leading-3">{d}</div>
              ))}
            </div>
            <div className="flex gap-1">
              {heatMapData.hourSlots.map((hour, colIdx) => (
                <div key={hour} className="flex flex-col gap-1">
                  <div className="h-4 text-[8px] text-muted-foreground text-center leading-3 mb-1">{hour}</div>
                  {heatMapData.weekday.map((_, rowIdx) => {
                    const value = heatMapData.data[rowIdx]?.[colIdx] || 0
                    return (
                      <div
                        key={`${rowIdx}-${colIdx}`}
                        className={cn(
                          'w-3 h-3 rounded-sm transition-colors',
                          getHeatColor(value),
                          value > 0 && 'cursor-default',
                        )}
                        title={`${heatMapData.weekday[rowIdx]} ${hour}: ${value} applications`}
                      />
                    )
                  })}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 mt-3">
          <span className="text-[10px] text-muted-foreground">Less</span>
          <div className="flex gap-0.5">
            {[0, 0.25, 0.5, 0.75, 1].map(v => (
              <div key={v} className={cn('w-3 h-3 rounded-sm', getHeatColor(v * maxVal))} />
            ))}
          </div>
          <span className="text-[10px] text-muted-foreground">More</span>
        </div>
      </CardContent>
    </Card>
  )
}
