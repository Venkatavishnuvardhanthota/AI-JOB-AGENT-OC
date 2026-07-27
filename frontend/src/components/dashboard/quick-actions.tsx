import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Link } from 'react-router-dom'
import {
  FilePlus,
  Search,
  Sparkles,
  FileText,
  History,
} from 'lucide-react'

const actions = [
  { label: 'Create Resume', icon: FilePlus, href: '/resumes', variant: 'default' as const },
  { label: 'Search Jobs', icon: Search, href: '/jobs/search', variant: 'outline' as const },
  { label: 'Match Jobs', icon: Sparkles, href: '/jobs/search', variant: 'outline' as const },
  { label: 'Generate Cover Letter', icon: FileText, href: '/applications', variant: 'outline' as const },
  { label: 'Application History', icon: History, href: '/applications', variant: 'outline' as const },
]

export function QuickActions() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-2">
          {actions.map((action) => {
            const Icon = action.icon
            return (
              <Button
                key={action.label}
                variant={action.variant}
                size="sm"
                className="justify-start gap-2 h-auto py-2.5"
                asChild
              >
                <Link to={action.href} aria-label={action.label}>
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  <span className="text-xs">{action.label}</span>
                </Link>
              </Button>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
