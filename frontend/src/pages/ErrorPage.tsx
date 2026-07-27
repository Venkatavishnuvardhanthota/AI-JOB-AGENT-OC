import { Link, useSearchParams } from 'react-router-dom'
import { AlertTriangle, WifiOff, ShieldAlert, ServerCrash, ArrowLeft, Home, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'

type ErrorCode = '500' | 'offline' | 'network' | 'permission' | 'generic'

const errorConfig: Record<ErrorCode, {
  icon: typeof AlertTriangle
  title: string
  description: string
  action?: { label: string; to?: string; onClick?: () => void }
}> = {
  '500': {
    icon: ServerCrash,
    title: 'Server error',
    description: 'Something went wrong on our end. Please try again later.',
    action: { label: 'Try again', onClick: () => window.location.reload() },
  },
  offline: {
    icon: WifiOff,
    title: 'You\'re offline',
    description: 'Check your internet connection and try again.',
    action: { label: 'Retry', onClick: () => window.location.reload() },
  },
  network: {
    icon: WifiOff,
    title: 'Network error',
    description: 'Unable to connect to our servers. Please check your connection.',
    action: { label: 'Retry', onClick: () => window.location.reload() },
  },
  permission: {
    icon: ShieldAlert,
    title: 'Permission denied',
    description: 'You do not have permission to access this resource.',
    action: { label: 'Go to Dashboard', to: '/dashboard' },
  },
  generic: {
    icon: AlertTriangle,
    title: 'Something went wrong',
    description: 'An unexpected error occurred. Please try again.',
    action: { label: 'Try again', onClick: () => window.location.reload() },
  },
}

export function ErrorPage() {
  const [searchParams] = useSearchParams()
  const code = (searchParams.get('code') as ErrorCode) || 'generic'
  const config = errorConfig[code] || errorConfig.generic
  const Icon = config.icon

  return (
    <div className="flex min-h-screen items-center justify-center bg-dark-900 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-error/20">
            <Icon className="h-8 w-8 text-error" />
          </div>
          <CardTitle className="text-xl">{config.title}</CardTitle>
          <CardDescription>{config.description}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {config.action && (
            config.action.to ? (
              <Link to={config.action.to}>
                <Button className="w-full gap-2">
                  <Home className="h-4 w-4" />
                  {config.action.label}
                </Button>
              </Link>
            ) : (
              <Button className="w-full gap-2" onClick={config.action.onClick}>
                <RefreshCw className="h-4 w-4" />
                {config.action.label}
              </Button>
            )
          )}
          <button
            onClick={() => window.history.back()}
            className="inline-flex w-full items-center justify-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Go back
          </button>
        </CardContent>
        <CardFooter className="justify-center">
          <Link to="/dashboard" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            Return home
          </Link>
        </CardFooter>
      </Card>
    </div>
  )
}
