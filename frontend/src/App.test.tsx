import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi } from 'vitest'

vi.mock('./pages/LoginPage', () => ({
  LoginPage: () => <div><h2>Welcome back</h2></div>,
}))

vi.mock('./pages/RegisterPage', () => ({
  RegisterPage: () => <div>Register</div>,
}))

vi.mock('./pages/ForgotPasswordPage', () => ({
  ForgotPasswordPage: () => <div>Forgot Password</div>,
}))

vi.mock('./pages/ResetPasswordPage', () => ({
  ResetPasswordPage: () => <div>Reset Password</div>,
}))

vi.mock('./pages/VerifyEmailPage', () => ({
  VerifyEmailPage: () => <div>Verify Email</div>,
}))

vi.mock('./pages/AuthSecurityPage', () => ({
  AuthSecurityPage: () => <div>Auth Security</div>,
}))

vi.mock('./pages/NotFoundPage', () => ({
  NotFoundPage: () => <div>404 Not Found</div>,
}))

vi.mock('./pages/ErrorPage', () => ({
  ErrorPage: () => <div>Error</div>,
}))

import App from './App'

describe('App', () => {
  it('renders the login page by default', async () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>,
    )
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /welcome back/i })).toBeInTheDocument()
    })
  })
})
