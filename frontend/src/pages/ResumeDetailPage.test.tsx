import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ToastProvider } from '@/components/ui/toast'
import { ResumeDetailPage } from './ResumeDetailPage'

const clientMock = vi.hoisted(() => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
  jobsApi: {},
  matchingApi: {},
}))

vi.mock('@/api/client', () => clientMock)

const resume = {
  id: 'r1',
  title: 'QA Hook Fix Resume',
  description: null,
  template: null,
  resume_type: 'standard',
  status: 'active',
  source: 'manual',
  origin: 'master',
  is_default: false,
  archived: false,
  version: 1,
  sections: [
    { id: 's1', section_type: 'summary', title: 'Summary', content: { text: 'Hello there' }, sort_order: 0 },
  ],
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

const sections = [
  { id: 's1', section_type: 'summary', title: 'Summary', content: { text: 'Hello there' }, sort_order: 0 },
]

let resumeData: any = resume

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  clientMock.api.get.mockImplementation(async (endpoint: string) => {
    if (endpoint === '/resumes/r1') return { success: true, data: resumeData }
    if (endpoint === '/resumes/r1/sections') return { success: true, data: sections }
    return { success: true, data: {} }
  })
  clientMock.api.post.mockResolvedValue({ success: true, data: {} })
  clientMock.api.patch.mockResolvedValue({ success: true, data: resume })
  clientMock.api.put.mockResolvedValue({ success: true, data: [] })
  clientMock.api.delete.mockResolvedValue(undefined)

  return render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <MemoryRouter initialEntries={['/resumes/r1']}>
          <Routes>
            <Route path="/resumes/:id" element={<ResumeDetailPage />} />
          </Routes>
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  )
}

describe('ResumeDetailPage hooks order', () => {
  beforeEach(() => {
    resumeData = resume
  })

  it('renders through the loading state into the loaded state without a hooks-order error', async () => {
    renderPage()

    const title = await screen.findByText('QA Hook Fix Resume')
    expect(title).toBeInTheDocument()
    expect(clientMock.api.get).toHaveBeenCalledWith('/resumes/r1')
    expect(clientMock.api.get).toHaveBeenCalledWith('/resumes/r1/sections')

    await waitFor(() => {
      expect(screen.getByText('Summary')).toBeInTheDocument()
    })
  })

  it('renders a not-found fallback when the resume does not exist', async () => {
    resumeData = null
    renderPage()
    expect(await screen.findByText('Resume not found')).toBeInTheDocument()
    const back = screen.getByRole('link', { name: /Back to Resume Library/i })
    expect(back).toBeInTheDocument()
  })
})