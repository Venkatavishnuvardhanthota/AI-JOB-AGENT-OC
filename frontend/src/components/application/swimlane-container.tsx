import { useMemo } from 'react'
import { getGroupKey, type GroupBy } from '@/services/pipeline'
import type { Application } from '@/types'

interface SwimlaneContainerProps {
  applications: Application[]
  groupBy: GroupBy
  renderCard: (app: Application) => React.ReactNode
}

export function SwimlaneContainer({ applications, groupBy, renderCard }: SwimlaneContainerProps) {
  const groups = useMemo(() => {
    const map = new Map<string, Application[]>()
    for (const app of applications) {
      const key = getGroupKey(app, groupBy)
      if (!map.has(key)) map.set(key, [])
      map.get(key)!.push(app)
    }
    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b))
  }, [applications, groupBy])

  return (
    <div className="space-y-4">
      {groups.map(([group, apps]) => (
        <div key={group} className="rounded-lg border border-glass-border bg-dark-900/50">
          <div className="flex items-center justify-between px-4 py-2 border-b border-glass-border">
            <h3 className="text-sm font-medium">{group}</h3>
            <span className="text-xs text-muted-foreground">{apps.length} application{apps.length !== 1 ? 's' : ''}</span>
          </div>
          <div className="p-4">
            {apps.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">No applications in this group</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                {apps.map(app => (
                  <div key={app.id}>{renderCard(app)}</div>
                ))}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
