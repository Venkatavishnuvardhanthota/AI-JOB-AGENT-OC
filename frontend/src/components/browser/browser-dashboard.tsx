import { useMemo } from 'react'
import { Card } from '@/components/ui/card'
import { browserFactory } from '@/services/browser/browser-factory'
import { Globe, Play, Square, AlertCircle } from 'lucide-react'

export function BrowserDashboard() {
  const stats = useMemo(() => {
    const browsers = browserFactory.listAll()
    const active = browsers.filter(b => b.status === 'running').length
    const totalErrors = browsers.reduce((s, b) => s + b.metrics.errors, 0)
    const totalActions = browsers.reduce((s, b) => s + b.metrics.actions, 0)
    return { total: browsers.length, active, totalErrors, totalActions }
  }, [])

  const cards = [
    { label: 'Total Browsers', value: stats.total, icon: Globe, color: 'text-blue-400' },
    { label: 'Active', value: stats.active, icon: Play, color: 'text-green-400' },
    { label: 'Actions', value: stats.totalActions, icon: Square, color: 'text-purple-400' },
    { label: 'Errors', value: stats.totalErrors, icon: AlertCircle, color: 'text-red-400' },
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
