import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { CheckCircle2, Clock } from 'lucide-react'
import { Link } from 'react-router-dom'

interface WelcomeBannerProps {
  onDismiss: () => void
}

export function WelcomeBanner({ onDismiss }: WelcomeBannerProps) {
  return (
    <Card className="relative overflow-hidden border-primary/20 bg-gradient-to-br from-dark-900 via-dark-800 to-primary/5">
      <CardContent className="p-6 md:p-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-4">
            <h1 className="text-2xl md:text-3xl font-bold text-foreground">
              Welcome to AI Job Agent
            </h1>
            <p className="text-muted-foreground max-w-lg">
              We'll help you land your next role. Here's what you can do:
            </p>
            <ul className="space-y-2">
              {[
                'Build your career profile',
                'Create or import resumes',
                'Find matching jobs',
                'Generate optimized applications',
                'Track your application progress',
              ].map((item) => (
                <li key={item} className="flex items-center gap-2 text-sm text-foreground/80">
                  <CheckCircle2 className="h-4 w-4 text-primary shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              Estimated setup time: 5-10 minutes
            </div>
          </div>
          <div className="flex flex-col gap-3 shrink-0">
            <Button size="lg" asChild>
              <Link to="/profile" onClick={onDismiss}>
                Get Started
              </Link>
            </Button>
            <Button variant="ghost" size="sm" onClick={onDismiss}>
              I'll explore on my own
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
