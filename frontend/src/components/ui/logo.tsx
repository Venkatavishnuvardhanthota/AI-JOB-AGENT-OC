import { cn } from '@/lib/utils'
import { Briefcase } from 'lucide-react'

interface LogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  showText?: boolean
  iconOnly?: boolean
  className?: string
}

const sizes = {
  sm: { box: 'h-7 w-7', icon: 'h-3.5 w-3.5', text: 'text-xs' },
  md: { box: 'h-8 w-8', icon: 'h-4 w-4', text: 'text-sm' },
  lg: { box: 'h-10 w-10', icon: 'h-5 w-5', text: 'text-base' },
  xl: { box: 'h-14 w-14', icon: 'h-7 w-7', text: 'text-xl' },
}

export function Logo({ size = 'md', showText = true, iconOnly = false, className }: LogoProps) {
  const s = sizes[size]

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className={cn(
        "flex items-center justify-center rounded-lg bg-gradient-to-br from-primary to-secondary text-white font-bold",
        s.box
      )}>
        {iconOnly ? (
          <Briefcase className={s.icon} />
        ) : (
          <span className={s.text}>AJ</span>
        )}
      </div>
      {showText && !iconOnly && (
        <span className={cn("font-semibold text-foreground", s.text)}>AI Job Agent</span>
      )}
    </div>
  )
}
