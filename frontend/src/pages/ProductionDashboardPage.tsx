import { PageHeader } from '@/components/layout/page-header'
import { ProductionDashboard } from '@/components/production/production-dashboard'

export function ProductionDashboardPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Production Dashboard"
        description="System observability, health monitoring, and operational control center."
      />
      <ProductionDashboard />
    </div>
  )
}
