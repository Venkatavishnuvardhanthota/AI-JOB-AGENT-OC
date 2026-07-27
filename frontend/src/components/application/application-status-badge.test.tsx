import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { ApplicationStatusBadge } from './application-status-badge'

describe('ApplicationStatusBadge', () => {
  it('renders status label', () => {
    render(<ApplicationStatusBadge status="applied" />)
    expect(screen.getByText('Applied')).toBeInTheDocument()
  })

  it('renders ready to apply', () => {
    render(<ApplicationStatusBadge status="ready_to_apply" />)
    expect(screen.getByText('Ready To Apply')).toBeInTheDocument()
  })

  it('renders technical interview', () => {
    render(<ApplicationStatusBadge status="technical_interview" />)
    expect(screen.getByText('Technical Interview')).toBeInTheDocument()
  })
})
