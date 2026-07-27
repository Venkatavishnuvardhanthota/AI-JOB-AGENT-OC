import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { UserPlus } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useToast } from '@/components/ui/toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { PasswordInput } from '@/components/auth/password-input'
import { AuthLayout } from '@/components/auth/auth-layout'

const registerSchema = z
  .object({
    firstName: z.string().min(1, 'First name is required').max(100),
    lastName: z.string().min(1, 'Last name is required').max(100),
    email: z.string().email('Please enter a valid email address'),
    password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Password must contain an uppercase letter')
      .regex(/[a-z]/, 'Password must contain a lowercase letter')
      .regex(/\d/, 'Password must contain a digit')
      .regex(/[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;'/`~]/, 'Password must contain a special character'),
    confirmPassword: z.string().min(1, 'Please confirm your password'),
    acceptTerms: z.literal(true, { message: 'You must accept the terms and conditions' }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })

type RegisterForm = z.infer<typeof registerSchema>

export function RegisterPage() {
  const navigate = useNavigate()
  const { register: registerUser } = useAuth()
  const { addToast } = useToast()
  const [serverError, setServerError] = useState('')

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      firstName: '',
      lastName: '',
      email: '',
      password: '',
      confirmPassword: '',
      acceptTerms: false as unknown as true,
    },
  })

  const onSubmit = async (data: RegisterForm) => {
    setServerError('')
    try {
      await registerUser(data.email, data.password, data.firstName, data.lastName)
      addToast('Account created successfully! Welcome aboard.', 'success')
      navigate('/dashboard')
    } catch (err) {
      setServerError(err instanceof Error ? err.message : 'Registration failed')
    }
  }

  return (
    <AuthLayout title="Create an account" subtitle="Get started with your AI-powered job search">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
        {serverError && (
          <div className="rounded-lg bg-error/10 border border-error/20 px-4 py-3 text-sm text-error" role="alert">
            {serverError}
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <label htmlFor="firstName" className="text-sm font-medium text-foreground">
              First name
            </label>
            <Input
              id="firstName"
              placeholder="John"
              autoComplete="given-name"
              aria-invalid={!!errors.firstName}
              {...register('firstName')}
            />
            {errors.firstName && (
              <p className="text-xs text-error" role="alert">{errors.firstName.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <label htmlFor="lastName" className="text-sm font-medium text-foreground">
              Last name
            </label>
            <Input
              id="lastName"
              placeholder="Doe"
              autoComplete="family-name"
              aria-invalid={!!errors.lastName}
              {...register('lastName')}
            />
            {errors.lastName && (
              <p className="text-xs text-error" role="alert">{errors.lastName.message}</p>
            )}
          </div>
        </div>

        <div className="space-y-2">
          <label htmlFor="reg-email" className="text-sm font-medium text-foreground">
            Email address
          </label>
          <Input
            id="reg-email"
            type="email"
            placeholder="name@example.com"
            autoComplete="email"
            aria-invalid={!!errors.email}
            {...register('email')}
          />
          {errors.email && (
            <p className="text-xs text-error" role="alert">{errors.email.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <label htmlFor="reg-password" className="text-sm font-medium text-foreground">
            Password
          </label>
          <PasswordInput
            id="reg-password"
            placeholder="Create a strong password"
            autoComplete="new-password"
            showStrength
            aria-invalid={!!errors.password}
            {...register('password')}
          />
          {errors.password && (
            <p className="text-xs text-error" role="alert">{errors.password.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <label htmlFor="confirmPassword" className="text-sm font-medium text-foreground">
            Confirm password
          </label>
          <PasswordInput
            id="confirmPassword"
            placeholder="Re-enter your password"
            autoComplete="new-password"
            showStrength={false}
            aria-invalid={!!errors.confirmPassword}
            {...register('confirmPassword')}
          />
          {errors.confirmPassword && (
            <p className="text-xs text-error" role="alert">{errors.confirmPassword.message}</p>
          )}
        </div>

        <div className="flex items-start gap-2">
          <input
            id="acceptTerms"
            type="checkbox"
            className="mt-1 h-4 w-4 rounded border-glass-border bg-dark-800 text-primary focus:ring-primary"
            {...register('acceptTerms')}
          />
          <label htmlFor="acceptTerms" className="text-sm text-muted-foreground cursor-pointer select-none">
            I accept the{' '}
            <Link to="/terms" className="text-primary hover:text-primary/80 transition-colors">Terms of Service</Link>
            {' '}and{' '}
            <Link to="/privacy" className="text-primary hover:text-primary/80 transition-colors">Privacy Policy</Link>
          </label>
        </div>
        {errors.acceptTerms && (
          <p className="text-xs text-error -mt-3" role="alert">{errors.acceptTerms.message}</p>
        )}

        <Button type="submit" className="w-full gap-2" disabled={isSubmitting}>
          {isSubmitting ? (
            <>
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              Creating account...
            </>
          ) : (
            <>
              <UserPlus className="h-4 w-4" />
              Create account
            </>
          )}
        </Button>

        <p className="text-center text-sm text-muted-foreground">
          Already have an account?{' '}
          <Link to="/login" className="text-primary hover:text-primary/80 font-medium transition-colors">
            Sign in
          </Link>
        </p>
      </form>
    </AuthLayout>
  )
}
