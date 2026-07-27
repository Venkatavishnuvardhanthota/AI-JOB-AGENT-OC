import { useState } from 'react'
import { Briefcase, Sparkles } from 'lucide-react'

interface AuthLayoutProps {
  children: React.ReactNode
  title: string
  subtitle?: string
}

const taglines = [
  'Your AI-powered job search assistant',
  'Find the perfect role with AI precision',
  'Smart applications, better results',
  'Let AI help you land your dream job',
]

export function AuthLayout({ children, title, subtitle }: AuthLayoutProps) {
  const [tagline] = useState(() => taglines[Math.floor(Math.random() * taglines.length)])

  return (
    <div className="flex min-h-screen">
      <div className="hidden lg:flex lg:w-1/2 relative flex-col items-center justify-center bg-gradient-to-br from-primary/20 via-dark-900 to-dark-800 p-12 overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-primary/10 via-transparent to-transparent" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_var(--tw-gradient-stops))] from-blue-500/5 via-transparent to-transparent" />
        <div className="relative z-10 flex flex-col items-center text-center max-w-md">
          <div className="mb-8 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/20 ring-1 ring-primary/30">
            <Briefcase className="h-8 w-8 text-primary" />
          </div>
          <h1 className="mb-3 text-3xl font-bold tracking-tight text-white">AI Job Agent</h1>
          <p className="text-lg text-muted-foreground">{tagline}</p>
          <div className="mt-12 grid grid-cols-3 gap-4 w-full">
            {[
              { label: 'Smart Matching', desc: 'AI-powered job recommendations' },
              { label: 'Auto-Apply', desc: 'Automated application workflows' },
              { label: 'AI Cover Letters', desc: 'Tailored letters in seconds' },
            ].map((feature) => (
              <div key={feature.label} className="rounded-lg bg-white/5 p-3 text-center ring-1 ring-white/10">
                <Sparkles className="mx-auto mb-1.5 h-4 w-4 text-primary" />
                <p className="text-xs font-medium text-white">{feature.label}</p>
                <p className="mt-0.5 text-[10px] text-muted-foreground">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="absolute bottom-8 left-0 right-0 z-10 text-center">
          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} AI Job Agent. All rights reserved.
          </p>
        </div>
      </div>

      <div className="flex w-full lg:w-1/2 flex-col items-center justify-center bg-dark-900 p-4 sm:p-8">
        <div className="w-full max-w-sm">
          <div className="lg:hidden mb-8 flex flex-col items-center text-center">
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/20 ring-1 ring-primary/30">
              <Briefcase className="h-6 w-6 text-primary" />
            </div>
            <h1 className="text-xl font-bold text-white">AI Job Agent</h1>
            <p className="mt-1 text-sm text-muted-foreground">{tagline}</p>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-semibold tracking-tight text-white">{title}</h2>
            {subtitle && <p className="mt-1.5 text-sm text-muted-foreground">{subtitle}</p>}
          </div>

          {children}
        </div>
      </div>
    </div>
  )
}
