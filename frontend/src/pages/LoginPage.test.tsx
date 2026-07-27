import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { LoginPage } from './LoginPage'
import { useToast } from '@/components/ui/toast'

vi.mock('@/context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

vi.mock('@/components/ui/toast', () => ({
  useToast: vi.fn(),
  ToastProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => vi.fn() }
})

import { useAuth } from '@/context/AuthContext'

function setup() {
  const mockLogin = vi.fn()
  const mockAddToast = vi.fn()
  const mockNavigate = vi.fn()

  vi.mocked(useAuth).mockReturnValue({
    login: mockLogin,
    isAuthenticated: false,
    isLoading: false,
    user: null,
    register: vi.fn(),
    logout: vi.fn(),
    forgotPassword: vi.fn(),
    resetPassword: vi.fn(),
    verifyEmail: vi.fn(),
    resendVerification: vi.fn(),
  } as unknown as ReturnType<typeof useAuth>)

  vi.mocked(useToast).mockReturnValue({ addToast: mockAddToast })

  const utils = render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>,
  )

  return { mockLogin, mockAddToast, mockNavigate, ...utils }
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders login form', () => {
    setup()
    expect(screen.getByLabelText('Email address')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('shows validation errors for empty fields', async () => {
    setup()
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    await waitFor(() => {
      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument()
    })
  })

  it('calls login on valid submission', async () => {
    const { mockLogin } = setup()
    fireEvent.input(screen.getByLabelText('Email address'), { target: { value: 'test@test.com' } })
    fireEvent.input(screen.getByLabelText('Password'), { target: { value: 'Password123!' } })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('test@test.com', 'Password123!', false)
    })
  })

  it('shows server error on login failure', async () => {
    const { mockLogin } = setup()
    mockLogin.mockRejectedValueOnce(new Error('Invalid credentials'))
    fireEvent.input(screen.getByLabelText('Email address'), { target: { value: 'test@test.com' } })
    fireEvent.input(screen.getByLabelText('Password'), { target: { value: 'wrong' } })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument()
    })
  })

  it('has link to register page', () => {
    setup()
    expect(screen.getByText("Don't have an account?")).toBeInTheDocument()
    expect(screen.getByText('Create one').closest('a')).toHaveAttribute('href', '/register')
  })

  it('has link to forgot password', () => {
    setup()
    expect(screen.getByText('Forgot password?').closest('a')).toHaveAttribute('href', '/forgot-password')
  })

  it('renders remember me checkbox', () => {
    setup()
    expect(screen.getByLabelText('Remember me')).toBeInTheDocument()
  })
})
