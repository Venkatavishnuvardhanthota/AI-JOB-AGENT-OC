import { Link, useSearchParams } from 'react-router-dom'
import { Clock, ShieldOff, Lock, ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

type SecurityState = 'session-expired' | '401' | '403'

const stateConfig: Record<SecurityState, {
  icon: typeof Clock
  title: string
  description: string
  action: { label: string; to: string }
}> = {
  'session-expired': {
    icon: Clock,
    title: 'Session expired',
    description: 'Your session has expired due to inactivity. Please sign in again to continue.',
    action: { label: 'Sign in again', to: '/login' },
  },
  '401': {
    icon: ShieldOff,
    title: 'Unauthorized',
    description: 'You need to be signed in to access this page. Please sign in to continue.',
    action: { label: 'Sign in', to: '/login' },
  },
  '403': {
    icon: Lock,
    title: 'Access denied',
    description: 'You do not have permission to access this page. If you believe this is an error, please contact support.',
    action: { label: 'Go to dashboard', to: '/dashboard' },
  },
}

export function AuthSecurityPage() {
  const [searchParams] = useSearchParams()
  const reason = (searchParams.get('reason') as SecurityState) || '401'
  const config = stateConfig[reason] || stateConfig['401']
  const Icon = config.icon

  return (
    <div className="flex min-h-screen items-center justify-center bg-dark-900 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-error/20">
            <Icon className="h-7 w-7 text-error" />
          </div>
          <CardTitle className="text-xl">{config.title}</CardTitle>
          <CardDescription>{config.description}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Link to={config.action.to} className="block">
            <Button className="w-full">{config.action.label}</Button>
          </Link>
          <Link
            to="/"
            className="inline-flex w-full items-center justify-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to home
          </Link>
        </CardContent>
      </Card>
    </div>
  )
}
