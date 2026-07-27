import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ForgotPasswordPage } from './ForgotPasswordPage'

vi.mock('@/context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

vi.mock('@/components/ui/toast', () => ({
  useToast: vi.fn(),
  ToastProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

import { useAuth } from '@/context/AuthContext'

function setup() {
  const mockForgotPassword = vi.fn()

  vi.mocked(useAuth).mockReturnValue({
    forgotPassword: mockForgotPassword,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    resetPassword: vi.fn(),
    verifyEmail: vi.fn(),
    resendVerification: vi.fn(),
    user: null,
    isAuthenticated: false,
    isLoading: false,
  } as unknown as ReturnType<typeof useAuth>)

  const utils = render(
    <MemoryRouter>
      <ForgotPasswordPage />
    </MemoryRouter>,
  )

  return { mockForgotPassword, ...utils }
}

describe('ForgotPasswordPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders forgot password form', () => {
    setup()
    expect(screen.getByText('Forgot password?')).toBeInTheDocument()
    expect(screen.getByLabelText('Email address')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /send reset link/i })).toBeInTheDocument()
  })

  it('shows validation error for invalid email', async () => {
    setup()
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }))
    await waitFor(() => {
      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument()
    })
  })

  it('shows success state after submission', async () => {
    const { mockForgotPassword } = setup()
    fireEvent.input(screen.getByLabelText('Email address'), { target: { value: 'test@test.com' } })
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }))
    await waitFor(() => {
      expect(mockForgotPassword).toHaveBeenCalledWith('test@test.com')
    })
    expect(screen.getByText('Check your email')).toBeInTheDocument()
    expect(screen.getByText(/We have sent a password reset link/)).toBeInTheDocument()
  })

  it('handles server error', async () => {
    const { mockForgotPassword } = setup()
    mockForgotPassword.mockRejectedValueOnce(new Error('Email not found'))
    fireEvent.input(screen.getByLabelText('Email address'), { target: { value: 'test@test.com' } })
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }))
    await waitFor(() => {
      expect(screen.getByText('Email not found')).toBeInTheDocument()
    })
  })

  it('has back to login link', () => {
    setup()
    expect(screen.getByText('Back to sign in').closest('a')).toHaveAttribute('href', '/login')
  })
})
