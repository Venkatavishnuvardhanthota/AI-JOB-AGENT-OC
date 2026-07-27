import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { Logo } from './logo'

describe('Logo', () => {
  it('renders AJ initials by default', () => {
    render(<Logo />)
    expect(screen.getByText('AJ')).toBeInTheDocument()
  })

  it('renders with text', () => {
    render(<Logo showText />)
    expect(screen.getByText('AI Job Agent')).toBeInTheDocument()
  })

  it('renders briefcase icon in iconOnly mode', () => {
    const { container } = render(<Logo iconOnly />)
    expect(container.querySelector('svg')).toBeInTheDocument()
  })
})
