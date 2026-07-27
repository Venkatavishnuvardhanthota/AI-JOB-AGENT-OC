import { Badge } from '@/components/ui/badge'
import type { ApplicationPriority } from '@/types'
import { PRIORITY_LABELS } from '@/services/status'
import { cn } from '@/lib/utils'

interface ApplicationPriorityBadgeProps {
  priority: ApplicationPriority
  className?: string
}

const colorMap: Record<string, string> = {
  critical: 'bg-error/20 text-error border-error/30',
  high: 'bg-warning/20 text-warning border-warning/30',
  medium: 'bg-primary/20 text-primary border-primary/30',
  low: 'bg-dark-600 text-muted-foreground border-glass-border',
}

export function ApplicationPriorityBadge({ priority, className }: ApplicationPriorityBadgeProps) {
  return (
    <Badge
      variant="outline"
      className={cn("capitalize border", colorMap[priority] || colorMap.low, className)}
    >
      {PRIORITY_LABELS[priority] || priority}
    </Badge>
  )
}
