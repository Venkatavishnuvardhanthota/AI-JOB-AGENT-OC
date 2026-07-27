import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { RegisterPage } from './RegisterPage'

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
import { useToast } from '@/components/ui/toast'

function setup() {
  const mockRegister = vi.fn()
  const mockAddToast = vi.fn()

  vi.mocked(useAuth).mockReturnValue({
    register: mockRegister,
    isAuthenticated: false,
    isLoading: false,
    user: null,
    login: vi.fn(),
    logout: vi.fn(),
    forgotPassword: vi.fn(),
    resetPassword: vi.fn(),
    verifyEmail: vi.fn(),
    resendVerification: vi.fn(),
  } as unknown as ReturnType<typeof useAuth>)

  vi.mocked(useToast).mockReturnValue({ addToast: mockAddToast })

  const utils = render(
    <MemoryRouter>
      <RegisterPage />
    </MemoryRouter>,
  )

  return { mockRegister, mockAddToast, ...utils }
}

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders registration form', () => {
    setup()
    expect(screen.getByLabelText('First name')).toBeInTheDocument()
    expect(screen.getByLabelText('Last name')).toBeInTheDocument()
    expect(screen.getByLabelText('Email address')).toBeInTheDocument()
    expect(screen.getByLabelText('Confirm password')).toBeInTheDocument()
    const passwordInputs = screen.getAllByLabelText('Password')
    expect(passwordInputs).toHaveLength(2)
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
  })

  it('shows validation errors for empty fields', async () => {
    setup()
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))
    await waitFor(() => {
      expect(screen.getByText('First name is required')).toBeInTheDocument()
      expect(screen.getByText('Last name is required')).toBeInTheDocument()
      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument()
      expect(screen.getByText('Password must be at least 8 characters')).toBeInTheDocument()
    })
  })

  it('shows password mismatch error', async () => {
    setup()
    fireEvent.input(screen.getByLabelText('First name'), { target: { value: 'John' } })
    fireEvent.input(screen.getByLabelText('Last name'), { target: { value: 'Doe' } })
    fireEvent.input(screen.getByLabelText('Email address'), { target: { value: 'test@test.com' } })
    fireEvent.input(screen.getAllByLabelText('Password')[0], { target: { value: 'Str0ng!Pass' } })
    fireEvent.input(screen.getByLabelText('Confirm password'), { target: { value: 'DifferentPass1!' } })
    fireEvent.click(screen.getByLabelText(/I accept the/))
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))
    await waitFor(() => {
      expect(screen.getByText('Passwords do not match')).toBeInTheDocument()
    })
  })

  it('calls register on valid submission', async () => {
    const { mockRegister } = setup()
    fireEvent.input(screen.getByLabelText('First name'), { target: { value: 'John' } })
    fireEvent.input(screen.getByLabelText('Last name'), { target: { value: 'Doe' } })
    fireEvent.input(screen.getByLabelText('Email address'), { target: { value: 'test@test.com' } })
    fireEvent.input(screen.getAllByLabelText('Password')[0], { target: { value: 'Str0ng!Pass' } })
    fireEvent.input(screen.getByLabelText('Confirm password'), { target: { value: 'Str0ng!Pass' } })
    fireEvent.click(screen.getByLabelText(/I accept the/))
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))
    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith('test@test.com', 'Str0ng!Pass', 'John', 'Doe')
    })
  })

  it('shows terms acceptance error when unchecked', async () => {
    setup()
    fireEvent.input(screen.getByLabelText('First name'), { target: { value: 'John' } })
    fireEvent.input(screen.getByLabelText('Last name'), { target: { value: 'Doe' } })
    fireEvent.input(screen.getByLabelText('Email address'), { target: { value: 'test@test.com' } })
    fireEvent.input(screen.getAllByLabelText('Password')[0], { target: { value: 'Str0ng!Pass' } })
    fireEvent.input(screen.getByLabelText('Confirm password'), { target: { value: 'Str0ng!Pass' } })
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))
    await waitFor(() => {
      expect(screen.getByText('You must accept the terms and conditions')).toBeInTheDocument()
    })
  })

  it('has link to login page', () => {
    setup()
    expect(screen.getByText('Already have an account?')).toBeInTheDocument()
    expect(screen.getByText('Sign in').closest('a')).toHaveAttribute('href', '/login')
  })
})
