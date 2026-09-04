import { Badge } from '@/components/ui/badge'

interface ProviderStatusBadgeProps {
  type: 'healthy' | 'configured' | 'enabled' | 'default' | 'disabled' | 'unavailable' | 'error'
  label?: string
}

const statusConfig: Record<string, { variant: 'success' | 'warning' | 'destructive' | 'default' | 'secondary' | 'outline'; label: string }> = {
  healthy: { variant: 'success', label: 'Healthy' },
  configured: { variant: 'success', label: 'Configured' },
  enabled: { variant: 'default', label: 'Enabled' },
  default: { variant: 'default', label: 'Default' },
  disabled: { variant: 'secondary', label: 'Disabled' },
  unavailable: { variant: 'warning', label: 'Unavailable' },
  error: { variant: 'destructive', label: 'Error' },
}

export function ProviderStatusBadge({ type, label }: ProviderStatusBadgeProps) {
  const config = statusConfig[type] || { variant: 'outline' as const, label: type }
  return <Badge variant={config.variant}>{label || config.label}</Badge>
}
