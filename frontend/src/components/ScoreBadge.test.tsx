import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { ScoreBadge } from './ScoreBadge'

describe('ScoreBadge', () => {
  it('renders score percentage', () => {
    render(<ScoreBadge score={0.85} />)
    expect(screen.getByText('85%')).toBeInTheDocument()
  })

  it('renders with label', () => {
    render(<ScoreBadge score={0.5} label="Match" />)
    expect(screen.getByText('Match')).toBeInTheDocument()
  })

  it('renders small size', () => {
    const { container } = render(<ScoreBadge score={0.3} size="sm" />)
    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('renders with zero score', () => {
    render(<ScoreBadge score={0} />)
    expect(screen.getByText('0%')).toBeInTheDocument()
  })

  it('renders with perfect score', () => {
    render(<ScoreBadge score={1} />)
    expect(screen.getByText('100%')).toBeInTheDocument()
  })
})
