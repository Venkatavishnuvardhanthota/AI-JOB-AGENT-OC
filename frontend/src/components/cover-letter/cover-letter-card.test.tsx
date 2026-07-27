import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect } from 'vitest'
import { CoverLetterCard } from './cover-letter-card'

const mockItem = {
  id: 'cl-1',
  title: 'Software Engineer Cover Letter',
  company_name: 'TechCo',
  job_title: 'Senior Engineer',
  template: 'modern',
  version: 2,
  status: 'ready',
  created_at: '2026-07-01T00:00:00Z',
  updated_at: '2026-07-15T00:00:00Z',
}

function renderCard(item = mockItem) {
  return render(
    <BrowserRouter>
      <CoverLetterCard item={item} />
    </BrowserRouter>,
  )
}

describe('CoverLetterCard', () => {
  it('renders title', () => {
    renderCard()
    expect(screen.getByText('Software Engineer Cover Letter')).toBeInTheDocument()
  })

  it('renders company name and job title', () => {
    renderCard()
    expect(screen.getByText(/techco/i)).toBeInTheDocument()
    expect(screen.getByText(/senior engineer/i)).toBeInTheDocument()
  })

  it('renders status badge', () => {
    renderCard()
    expect(screen.getByText('ready')).toBeInTheDocument()
  })

  it('renders template badge', () => {
    renderCard()
    expect(screen.getByText('modern')).toBeInTheDocument()
  })

  it('renders with draft status', () => {
    renderCard({ ...mockItem, status: 'draft' })
    expect(screen.getByText('draft')).toBeInTheDocument()
  })

  it('renders without company when not provided', () => {
    const { company_name, ...rest } = mockItem
    renderCard(rest as any)
    expect(screen.queryByText(/techco/i)).not.toBeInTheDocument()
  })

  it('links to detail page', () => {
    renderCard()
    const link = screen.getByRole('link', { name: /software engineer cover letter/i })
    expect(link).toHaveAttribute('href', '/cover-letters/cl-1')
  })
})
