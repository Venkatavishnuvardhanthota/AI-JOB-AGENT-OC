import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Lock, CheckCircle, AlertCircle } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { Button } from '@/components/ui/button'
import { PasswordInput } from '@/components/auth/password-input'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'

const resetSchema = z
  .object({
    password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Password must contain an uppercase letter')
      .regex(/[a-z]/, 'Password must contain a lowercase letter')
      .regex(/\d/, 'Password must contain a digit')
      .regex(/[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;'/`~]/, 'Password must contain a special character'),
    confirmPassword: z.string().min(1, 'Please confirm your password'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })

type ResetForm = z.infer<typeof resetSchema>

export function ResetPasswordPage() {
  const { resetPassword } = useAuth()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const [success, setSuccess] = useState(false)
  const [serverError, setServerError] = useState('')

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetForm>({
    resolver: zodResolver(resetSchema),
  })

  const onSubmit = async (data: ResetForm) => {
    if (!token) return
    setServerError('')
    try {
      await resetPassword(token, data.password)
      setSuccess(true)
    } catch (err) {
      setServerError(err instanceof Error ? err.message : 'Failed to reset password')
    }
  }

  if (!token) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-dark-900 p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-error/20">
              <AlertCircle className="h-6 w-6 text-error" />
            </div>
            <CardTitle className="text-xl">Invalid reset link</CardTitle>
            <CardDescription>
              This password reset link is invalid or has expired. Please request a new one.
            </CardDescription>
          </CardHeader>
          <CardFooter className="justify-center">
            <Link to="/forgot-password" className="text-sm text-primary hover:text-primary/80 transition-colors">
              Request a new reset link
            </Link>
          </CardFooter>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-dark-900 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/20">
            {success ? (
              <CheckCircle className="h-6 w-6 text-success" />
            ) : (
              <Lock className="h-6 w-6 text-primary" />
            )}
          </div>
          <CardTitle className="text-xl">
            {success ? 'Password reset successful' : 'Reset your password'}
          </CardTitle>
          <CardDescription>
            {success
              ? 'Your password has been updated successfully.'
              : 'Enter your new password below.'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!success ? (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
              {serverError && (
                <div className="rounded-lg bg-error/10 border border-error/20 px-4 py-3 text-sm text-error" role="alert">
                  {serverError}
                </div>
              )}
              <div className="space-y-2">
                <label htmlFor="reset-password" className="text-sm font-medium text-foreground">
                  New password
                </label>
                <PasswordInput
                  id="reset-password"
                  placeholder="Enter new password"
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
                <label htmlFor="reset-confirm" className="text-sm font-medium text-foreground">
                  Confirm new password
                </label>
                <PasswordInput
                  id="reset-confirm"
                  placeholder="Re-enter new password"
                  autoComplete="new-password"
                  showStrength={false}
                  aria-invalid={!!errors.confirmPassword}
                  {...register('confirmPassword')}
                />
                {errors.confirmPassword && (
                  <p className="text-xs text-error" role="alert">{errors.confirmPassword.message}</p>
                )}
              </div>
              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    Resetting...
                  </>
                ) : (
                  'Reset password'
                )}
              </Button>
            </form>
          ) : (
            <p className="text-center text-sm text-muted-foreground">
              You can now sign in with your new password.
            </p>
          )}
        </CardContent>
        <CardFooter className="justify-center">
          <Link
            to="/login"
            className="inline-flex items-center gap-1.5 text-sm text-primary hover:text-primary/80 transition-colors"
          >
            Sign in with new password
          </Link>
        </CardFooter>
      </Card>
    </div>
  )
}
