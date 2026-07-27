import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { PasswordStrength } from './password-strength'

describe('PasswordStrength', () => {
  it('renders nothing when password is empty', () => {
    const { container } = render(<PasswordStrength password="" />)
    expect(container.firstChild).toBeNull()
  })

  it('shows Weak for a short password', () => {
    render(<PasswordStrength password="ab" />)
    expect(screen.getByText('Weak')).toBeInTheDocument()
  })

  it('shows Fair for password meeting 2 requirements', () => {
    render(<PasswordStrength password="abcdefgh" />)
    expect(screen.getByText('Fair')).toBeInTheDocument()
  })

  it('shows Good for password meeting 3 requirements', () => {
    render(<PasswordStrength password="Abcdefgh" />)
    expect(screen.getByText('Good')).toBeInTheDocument()
  })

  it('shows Strong for password meeting 4 requirements', () => {
    render(<PasswordStrength password="Abcdefgh1" />)
    expect(screen.getByText('Strong')).toBeInTheDocument()
  })

  it('shows Very Strong for meeting all 5 requirements', () => {
    render(<PasswordStrength password="Abcdef12!@" />)
    expect(screen.getByText('Very Strong')).toBeInTheDocument()
  })

  it('renders all requirement checklist items', () => {
    render(<PasswordStrength password="Test1234!" />)
    expect(screen.getByText('At least 8 characters')).toBeInTheDocument()
    expect(screen.getByText('One uppercase letter')).toBeInTheDocument()
    expect(screen.getByText('One lowercase letter')).toBeInTheDocument()
    expect(screen.getByText('One digit')).toBeInTheDocument()
    expect(screen.getByText('One special character')).toBeInTheDocument()
  })

  it('marks requirements as passed', () => {
    render(<PasswordStrength password="Test1234!" />)
    const checks = screen.getAllByText('✓')
    expect(checks.length).toBe(5)
  })
})
