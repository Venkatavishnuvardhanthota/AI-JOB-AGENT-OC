import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ToastProvider } from '@/components/ui/toast'
import { describe, it, expect } from 'vitest'
import { ApplicationCard } from './application-card'
import type { Application } from '@/types'

const qc = new QueryClient({
  defaultOptions: { queries: { retry: false } },
})

function TestWrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <MemoryRouter>
          {children}
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>
  )
}

const mockApp: Application = {
  id: '1',
  user_id: 'u1',
  job_id: 'j1',
  job_title: 'Software Engineer',
  company_name: 'Tech Corp',
  status: 'applied',
  priority: 'high',
  location: 'San Francisco, CA',
  created_at: '2024-01-15T00:00:00Z',
  updated_at: '2024-01-15T00:00:00Z',
}

describe('ApplicationCard', () => {
  it('renders job title', () => {
    render(<TestWrapper><ApplicationCard application={mockApp} /></TestWrapper>)
    expect(screen.getByText('Software Engineer')).toBeInTheDocument()
  })

  it('renders company name', () => {
    render(<TestWrapper><ApplicationCard application={mockApp} /></TestWrapper>)
    expect(screen.getByText('Tech Corp')).toBeInTheDocument()
  })

  it('renders location', () => {
    render(<TestWrapper><ApplicationCard application={mockApp} /></TestWrapper>)
    expect(screen.getByText('San Francisco, CA')).toBeInTheDocument()
  })

  it('renders status badge', () => {
    render(<TestWrapper><ApplicationCard application={mockApp} /></TestWrapper>)
    expect(screen.getByText('Applied')).toBeInTheDocument()
  })
})
