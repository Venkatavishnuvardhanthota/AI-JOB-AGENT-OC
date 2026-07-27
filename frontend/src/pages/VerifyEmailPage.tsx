import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { CheckCircle, XCircle, Loader2, RefreshCw } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useToast } from '@/components/ui/toast'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'

export function VerifyEmailPage() {
  const { verifyEmail, resendVerification } = useAuth()
  const { addToast } = useToast()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const email = searchParams.get('email')
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying')
  const [errorMessage, setErrorMessage] = useState('')
  const [resending, setResending] = useState(false)

  useEffect(() => {
    if (token) {
      verifyEmail(token)
        .then(() => setStatus('success'))
        .catch((err) => {
          setStatus('error')
          setErrorMessage(err instanceof Error ? err.message : 'Verification failed')
        })
    } else {
      setStatus('error')
      setErrorMessage('No verification token provided.')
    }
  }, [token, verifyEmail])

  const handleResend = async () => {
    if (!email) return
    setResending(true)
    try {
      await resendVerification(email)
      addToast('Verification email resent successfully.', 'success')
    } catch {
      addToast('Failed to resend verification email.', 'error')
    } finally {
      setResending(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-dark-900 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full"
            style={{
              background: status === 'verifying' ? 'rgba(59,130,246,0.2)' : status === 'success' ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)',
            }}
          >
            {status === 'verifying' && <Loader2 className="h-6 w-6 text-primary animate-spin" />}
            {status === 'success' && <CheckCircle className="h-6 w-6 text-success" />}
            {status === 'error' && <XCircle className="h-6 w-6 text-error" />}
          </div>
          <CardTitle className="text-xl">
            {status === 'verifying' && 'Verifying your email...'}
            {status === 'success' && 'Email verified!'}
            {status === 'error' && 'Verification failed'}
          </CardTitle>
          <CardDescription>
            {status === 'success' && 'Your email address has been verified successfully.'}
            {status === 'error' && errorMessage}
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center">
          {status === 'success' && (
            <Link to="/dashboard">
              <Button className="w-full">Go to dashboard</Button>
            </Link>
          )}
          {status === 'error' && email && (
            <Button variant="outline" className="w-full gap-2" onClick={handleResend} disabled={resending}>
              <RefreshCw className={`h-4 w-4 ${resending ? 'animate-spin' : ''}`} />
              {resending ? 'Resending...' : 'Resend verification email'}
            </Button>
          )}
        </CardContent>
        <CardFooter className="justify-center">
          <Link to="/login" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            Back to sign in
          </Link>
        </CardFooter>
      </Card>
    </div>
  )
}
