import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi } from 'vitest'
import { ApplicationsPage } from './ApplicationsPage'

vi.mock('@/services/application', () => ({
  applicationService: {
    list: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20, total_pages: 1 }),
    getStats: vi.fn().mockResolvedValue({
      total: 0, applied_this_week: 0, interviews: 0, offers: 0,
      acceptance_rate: 0, response_rate: 0, upcoming_deadlines: 0, recent_activity: 0,
      by_status: {}, by_priority: {},
    }),
  },
}))

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <ApplicationsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ApplicationsPage', () => {
  it('renders page title', async () => {
    renderPage()
    expect(await screen.findByText('Applications')).toBeInTheDocument()
  })

  it('shows empty state when no applications', async () => {
    renderPage()
    expect(await screen.findByText('No applications yet')).toBeInTheDocument()
  })
})
