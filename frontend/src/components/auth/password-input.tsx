import { forwardRef, useState } from 'react'
import { Eye, EyeOff, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Input } from '@/components/ui/input'
import { PasswordStrength } from './password-strength'

interface PasswordInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  showStrength?: boolean
  showCapsLock?: boolean
}

export const PasswordInput = forwardRef<HTMLInputElement, PasswordInputProps>(
  ({ className, showStrength, showCapsLock = true, ...props }, ref) => {
    const [showPassword, setShowPassword] = useState(false)
    const [capsLock, setCapsLock] = useState(false)

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (showCapsLock && e.getModifierState) {
        setCapsLock(e.getModifierState('CapsLock'))
      }
      props.onKeyDown?.(e)
    }

    const handleKeyUp = (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (showCapsLock && e.getModifierState) {
        setCapsLock(e.getModifierState('CapsLock'))
      }
      props.onKeyUp?.(e)
    }

    return (
      <div className="space-y-2">
        <div className="relative">
          <Input
            ref={ref}
            type={showPassword ? 'text' : 'password'}
            className={cn('pr-10', className)}
            aria-label={props['aria-label'] || 'Password'}
            onKeyDown={handleKeyDown}
            onKeyUp={handleKeyUp}
            {...props}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            tabIndex={-1}
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
        {capsLock && (
          <div className="flex items-center gap-1.5 text-xs text-warning" role="alert">
            <AlertTriangle className="h-3.5 w-3.5" />
            <span>Caps Lock is on</span>
          </div>
        )}
        {showStrength && props.value && typeof props.value === 'string' && (
          <PasswordStrength password={props.value} />
        )}
      </div>
    )
  },
)
PasswordInput.displayName = 'PasswordInput'
