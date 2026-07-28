import { useMemo } from 'react'
import { Card } from '@/components/ui/card'
import { applicationGenerationService } from '@/services/application-generation/application-generation'
import { FileText, CheckCircle, AlertTriangle, TrendingUp } from 'lucide-react'

export function GenerationDashboard() {
  const stats = useMemo(() => applicationGenerationService.getStatistics(), [])

  const cards = [
    { label: 'Total Packages', value: stats.totalPackages, icon: FileText, color: 'text-blue-400' },
    { label: 'Ready to Apply', value: stats.readyToApply, icon: CheckCircle, color: 'text-green-400' },
    { label: 'Needs Review', value: stats.needsReview, icon: AlertTriangle, color: 'text-yellow-400' },
    { label: 'Avg Confidence', value: `${stats.averageConfidence}%`, icon: TrendingUp, color: 'text-purple-400' },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map(card => (
        <Card key={card.label} className="p-4 flex items-center gap-3">
          <card.icon className={`h-8 w-8 ${card.color}`} />
          <div>
            <p className="text-2xl font-bold">{card.value}</p>
            <p className="text-xs text-muted-foreground">{card.label}</p>
          </div>
        </Card>
      ))}
    </div>
  )
}
