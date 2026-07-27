import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { ApplicationPriorityBadge } from './application-priority-badge'

describe('ApplicationPriorityBadge', () => {
  it('renders critical priority', () => {
    render(<ApplicationPriorityBadge priority="critical" />)
    expect(screen.getByText('Critical')).toBeInTheDocument()
  })

  it('renders low priority', () => {
    render(<ApplicationPriorityBadge priority="low" />)
    expect(screen.getByText('Low')).toBeInTheDocument()
  })
})
