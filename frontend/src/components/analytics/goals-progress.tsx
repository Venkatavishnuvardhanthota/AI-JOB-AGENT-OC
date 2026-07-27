import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { Goal } from '@/services/analytics'
import { Target, Edit2, Check, X, TrendingUp } from 'lucide-react'

interface GoalsProgressProps {
  goals: Goal[]
  onUpdate: (goals: Goal[]) => void
  loading: boolean
}

export function GoalsProgress({ goals, onUpdate, loading }: GoalsProgressProps) {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')

  if (loading) {
    return <Card><CardContent className="p-6"><div className="h-40 bg-dark-700 rounded animate-pulse" /></CardContent></Card>
  }

  const handleEdit = (goal: Goal) => {
    setEditingId(goal.id)
    setEditValue(String(goal.target))
  }

  const handleSave = (goal: Goal) => {
    const val = parseInt(editValue)
    if (!isNaN(val) && val > 0) {
      onUpdate(goals.map(g => g.id === goal.id ? { ...g, target: val } : g))
    }
    setEditingId(null)
  }

  const allComplete = goals.every(g => g.current >= g.target)
  const totalProgress = goals.length > 0
    ? Math.round(goals.reduce((sum, g) => sum + Math.min(g.current / g.target, 1), 0) / goals.length * 100)
    : 0

  const goalIcons: Record<string, React.ElementType> = {
    applications: Target,
    interviews: TrendingUp,
    offers: TrendingUp,
    acceptances: Check,
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Goals & Progress
          {allComplete && goals.length > 0 && (
            <Badge variant="default" className="text-xs">All goals complete!</Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="mb-2">
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-muted-foreground">Overall Progress</span>
            <span className="font-medium">{totalProgress}%</span>
          </div>
          <div className="h-2 rounded-full bg-dark-700 overflow-hidden">
            <div
              className={cn('h-full rounded-full transition-all duration-500', totalProgress === 100 ? 'bg-green-500' : 'bg-primary')}
              style={{ width: `${totalProgress}%` }}
            />
          </div>
        </div>

        {goals.map(goal => {
          const pct = goal.target > 0 ? Math.min(Math.round((goal.current / goal.target) * 100), 100) : 0
          const Icon = goalIcons[goal.type] || Target
          return (
            <div key={goal.id}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <Icon className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-sm font-medium">{goal.label}</span>
                  {goal.current >= goal.target && (
                    <Check className="h-3.5 w-3.5 text-green-400" />
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {editingId === goal.id ? (
                    <div className="flex items-center gap-1">
                      <Input
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter') handleSave(goal); if (e.key === 'Escape') setEditingId(null) }}
                        className="h-6 w-16 text-xs"
                        autoFocus
                      />
                      <button onClick={() => handleSave(goal)} className="p-0.5 hover:text-foreground"><Check className="h-3 w-3" /></button>
                      <button onClick={() => setEditingId(null)} className="p-0.5 hover:text-foreground"><X className="h-3 w-3" /></button>
                    </div>
                  ) : (
                    <>
                      <span className="text-sm font-medium tabular-nums">
                        {goal.current}/{goal.target}
                      </span>
                      <button onClick={() => handleEdit(goal)} className="p-0.5 opacity-0 hover:opacity-100 transition-opacity" aria-label={`Edit ${goal.label} target`}>
                        <Edit2 className="h-3 w-3 text-muted-foreground" />
                      </button>
                    </>
                  )}
                </div>
              </div>
              <div className="h-2 rounded-full bg-dark-700 overflow-hidden">
                <div
                  className={cn('h-full rounded-full transition-all duration-500', pct === 100 ? 'bg-green-500' : 'bg-primary/50')}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
