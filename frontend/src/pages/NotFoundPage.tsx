import { Link } from 'react-router-dom'
import { FileQuestion, ArrowLeft, Home } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-dark-900 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-warning/20">
            <FileQuestion className="h-8 w-8 text-warning" />
          </div>
          <CardTitle className="text-4xl font-bold">404</CardTitle>
          <CardTitle className="text-xl mt-2">Page not found</CardTitle>
          <CardDescription>
            The page you are looking for doesn&apos;t exist or has been moved.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Link to="/dashboard">
            <Button className="w-full gap-2">
              <Home className="h-4 w-4" />
              Go to Dashboard
            </Button>
          </Link>
          <button
            onClick={() => window.history.back()}
            className="inline-flex w-full items-center justify-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Go back
          </button>
        </CardContent>
        <CardFooter className="justify-center text-xs text-muted-foreground">
          If you believe this is an error, please contact support.
        </CardFooter>
      </Card>
    </div>
  )
}
