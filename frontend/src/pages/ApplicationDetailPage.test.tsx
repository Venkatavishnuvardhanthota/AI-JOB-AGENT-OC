import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi } from 'vitest'
import { ToastProvider } from '@/components/ui/toast'
import { ApplicationDetailPage } from './ApplicationDetailPage'

vi.mock('@/services/application', () => ({
  applicationService: {
    get: vi.fn().mockResolvedValue({
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
    }),
  },
}))

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <MemoryRouter initialEntries={['/applications/1']}>
          <Routes>
            <Route path="/applications/:id" element={<ApplicationDetailPage />} />
          </Routes>
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  )
}

describe('ApplicationDetailPage', () => {
  it('renders job title', async () => {
    renderPage()
    expect(await screen.findByText('Software Engineer')).toBeInTheDocument()
  })

  it('renders company name', async () => {
    renderPage()
    expect(await screen.findByText('Tech Corp')).toBeInTheDocument()
  })

  it('renders overview tab by default', async () => {
    renderPage()
    expect(await screen.findByText('Job Information')).toBeInTheDocument()
  })

  it('renders all tab triggers', async () => {
    renderPage()
    expect(await screen.findByText('Timeline')).toBeInTheDocument()
    expect(screen.getByText('Documents')).toBeInTheDocument()
    expect(screen.getByText('Notes')).toBeInTheDocument()
    expect(screen.getByText('Activity')).toBeInTheDocument()
  })
})
