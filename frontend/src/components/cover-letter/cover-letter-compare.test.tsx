import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { CoverLetterCompare } from './cover-letter-compare'

describe('CoverLetterCompare', () => {
  it('renders with matching content', () => {
    render(<CoverLetterCompare original="Hello World" edited="Hello World" />)
    expect(screen.getByText('No differences found between versions.')).toBeInTheDocument()
  })

  it('detects added content', () => {
    render(<CoverLetterCompare original="Hello" edited="Hello World" />)
    expect(screen.getByText(/changes detected/i)).toBeInTheDocument()
  })

  it('renders both panels with labels', () => {
    render(<CoverLetterCompare original="A" edited="B" labelA="Original" labelB="Edited" />)
    expect(screen.getByText('Original')).toBeInTheDocument()
    expect(screen.getByText('Edited')).toBeInTheDocument()
  })

  it('shows sync toggle', () => {
    render(<CoverLetterCompare original="A" edited="B" />)
    expect(screen.getByText('Sync: On')).toBeInTheDocument()
  })

  it('handles empty content', () => {
    render(<CoverLetterCompare original="" edited="" />)
    expect(screen.getByText('No differences found between versions.')).toBeInTheDocument()
  })
})
