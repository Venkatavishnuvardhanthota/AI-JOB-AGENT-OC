import { Badge } from '@/components/ui/badge'
import type { ApplicationStatus } from '@/types'
import { getStatusLabel, getStatusCategory } from '@/services/status'
import { cn } from '@/lib/utils'

interface ApplicationStatusBadgeProps {
  status: ApplicationStatus
  className?: string
}

const variantMap: Record<string, 'default' | 'secondary' | 'success' | 'warning' | 'destructive'> = {
  preparation: 'secondary',
  active: 'warning',
  interview: 'default',
  offer: 'success',
  final: 'destructive',
}

export function ApplicationStatusBadge({ status, className }: ApplicationStatusBadgeProps) {
  const category = getStatusCategory(status)
  const variant = variantMap[category] || 'secondary'

  return (
    <Badge variant={variant} className={cn("capitalize", className)}>
      {getStatusLabel(status)}
    </Badge>
  )
}
