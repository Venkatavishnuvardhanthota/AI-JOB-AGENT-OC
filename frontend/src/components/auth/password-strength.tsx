import { useMemo } from 'react'
import { cn } from '@/lib/utils'
import { Progress } from '@/components/ui/progress'

interface PasswordStrengthProps {
  password: string
}

interface Requirement {
  label: string
  test: (p: string) => boolean
}

const requirements: Requirement[] = [
  { label: 'At least 8 characters', test: (p) => p.length >= 8 },
  { label: 'One uppercase letter', test: (p) => /[A-Z]/.test(p) },
  { label: 'One lowercase letter', test: (p) => /[a-z]/.test(p) },
  { label: 'One digit', test: (p) => /\d/.test(p) },
  { label: 'One special character', test: (p) => /[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;'/`~]/.test(p) },
]

function getStrength(password: string): { score: number; label: string; color: string } {
  const passed = requirements.filter((r) => r.test(password)).length
  if (password.length === 0) return { score: 0, label: '', color: 'bg-dark-700' }
  if (passed <= 1) return { score: 20, label: 'Weak', color: 'bg-error' }
  if (passed <= 2) return { score: 40, label: 'Fair', color: 'bg-warning' }
  if (passed <= 3) return { score: 60, label: 'Good', color: 'bg-yellow-500' }
  if (passed <= 4) return { score: 80, label: 'Strong', color: 'bg-green-500' }
  return { score: 100, label: 'Very Strong', color: 'bg-green-500' }
}

export function PasswordStrength({ password }: PasswordStrengthProps) {
  const { score, label, color } = useMemo(() => getStrength(password), [password])

  if (!password) return null

  return (
    <div className="space-y-2" role="region" aria-label="Password strength">
      <Progress value={score} className={cn('h-1.5', color)} aria-label={`Password strength: ${label}`} />
      <p className="text-xs text-muted-foreground" aria-live="polite">
        Strength: <span className={cn('font-medium', score >= 60 ? 'text-green-500' : score >= 40 ? 'text-warning' : 'text-error')}>{label}</span>
      </p>
      <ul className="space-y-1" aria-label="Password requirements">
        {requirements.map((req) => {
          const passed = req.test(password)
          return (
            <li key={req.label} className="flex items-center gap-1.5 text-xs">
              <span
                className={cn(
                  'flex h-3.5 w-3.5 items-center justify-center rounded-full text-[10px] font-bold',
                  passed ? 'bg-success/20 text-success' : 'bg-dark-700 text-muted-foreground',
                )}
                aria-hidden="true"
              >
                {passed ? '✓' : '×'}
              </span>
              <span className={passed ? 'text-foreground' : 'text-muted-foreground'}>{req.label}</span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
