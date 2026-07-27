import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { AlertCircle, AlertTriangle, AlertOctagon } from 'lucide-react'
import type { ColumnValidation, ColumnRuleResult } from '@/services/pipeline'

interface WipIndicatorsProps {
  validation: ColumnValidation
  collapsed?: boolean
  rules?: ColumnRuleResult[]
}

export function WipIndicators({ validation, collapsed, rules }: WipIndicatorsProps) {
  return (
    <div className={cn('flex flex-wrap gap-1', collapsed && 'flex-col')}>
      <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4 gap-0.5">
        {validation.total}
      </Badge>
      {validation.highPriority > 0 && (
        <Badge variant="destructive" className="text-[10px] px-1.5 py-0 h-4 gap-0.5">
          <AlertTriangle className="h-2.5 w-2.5" />
          {validation.highPriority}
        </Badge>
      )}
      {validation.overdue > 0 && (
        <Badge variant="warning" className="text-[10px] px-1.5 py-0 h-4 gap-0.5">
          <AlertCircle className="h-2.5 w-2.5" />
          {validation.overdue}
        </Badge>
      )}
      {validation.interviewsScheduled > 0 && (
        <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-4 gap-0.5">
          {validation.interviewsScheduled} int
        </Badge>
      )}
      {validation.offers > 0 && (
        <Badge variant="default" className="text-[10px] px-1.5 py-0 h-4 gap-0.5">
          {validation.offers} off
        </Badge>
      )}
      {rules && rules.length > 0 && (
        <div className="w-full mt-1 space-y-0.5">
          {rules.map((r, i) => (
            <div key={i} className={cn(
              'flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded',
              r.severity === 'critical' && 'bg-error/10 text-error',
              r.severity === 'warning' && 'bg-warning/10 text-warning',
              r.severity === 'info' && 'bg-info/10 text-info',
            )}>
              {r.severity === 'critical' && <AlertOctagon className="h-2.5 w-2.5" />}
              {r.severity === 'warning' && <AlertTriangle className="h-2.5 w-2.5" />}
              {r.severity === 'info' && <AlertCircle className="h-2.5 w-2.5" />}
              {r.message}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
