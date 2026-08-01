import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { ProviderStatusBadge } from '../ProviderStatusBadge'

describe('ProviderStatusBadge', () => {
  it('renders healthy badge', () => {
    render(<ProviderStatusBadge type="healthy" />)
    expect(screen.getByText('Healthy')).toBeInTheDocument()
  })

  it('renders configured badge', () => {
    render(<ProviderStatusBadge type="configured" />)
    expect(screen.getByText('Configured')).toBeInTheDocument()
  })

  it('renders enabled badge', () => {
    render(<ProviderStatusBadge type="enabled" />)
    expect(screen.getByText('Enabled')).toBeInTheDocument()
  })

  it('renders default badge', () => {
    render(<ProviderStatusBadge type="default" />)
    expect(screen.getByText('Default')).toBeInTheDocument()
  })

  it('renders disabled badge', () => {
    render(<ProviderStatusBadge type="disabled" />)
    expect(screen.getByText('Disabled')).toBeInTheDocument()
  })

  it('renders unavailable badge', () => {
    render(<ProviderStatusBadge type="unavailable" />)
    expect(screen.getByText('Unavailable')).toBeInTheDocument()
  })

  it('renders error badge', () => {
    render(<ProviderStatusBadge type="error" />)
    expect(screen.getByText('Error')).toBeInTheDocument()
  })

  it('uses custom label when provided', () => {
    render(<ProviderStatusBadge type="error" label="Custom Error" />)
    expect(screen.getByText('Custom Error')).toBeInTheDocument()
  })
})
