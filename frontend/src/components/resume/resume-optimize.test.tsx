import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ToastProvider } from '@/components/ui/toast'
import { ResumeOptimize } from './resume-optimize'

const hooksMock = vi.hoisted(() => ({
  useOptimizeResume: vi.fn(),
  useAnalyzeResume: vi.fn(),
  useJobs: vi.fn(),
}))

vi.mock('@/api/hooks', () => hooksMock)

describe('ResumeOptimize', () => {
  beforeEach(() => {
    hooksMock.useOptimizeResume.mockReturnValue({ mutateAsync: vi.fn() })
    hooksMock.useAnalyzeResume.mockReturnValue({ mutateAsync: vi.fn() })
  })

  it('renders job options when useJobs returns the flat paginated shape (no data wrapper)', async () => {
    hooksMock.useJobs.mockReturnValue({
      data: {
        success: true,
        items: [
          { id: 'j1', title: 'Senior Engineer', company: 'ACME' },
          { id: 'j2', title: 'Staff Engineer', company: 'Globex' },
        ],
        total: 2,
        page: 1,
        page_size: 20,
        total_pages: 1,
      },
    })

    render(
      <ToastProvider>
        <ResumeOptimize resumeId="r1" resumeTitle="QA Resume" onOptimized={() => {}} />
      </ToastProvider>,
    )

    expect(await screen.findByText('Senior Engineer')).toBeInTheDocument()
    expect(screen.getByText('Staff Engineer')).toBeInTheDocument()
    expect(screen.getByText('ACME')).toBeInTheDocument()
  })

  it('renders the empty state without crashing when there are no jobs', () => {
    hooksMock.useJobs.mockReturnValue({ data: undefined })

    render(
      <ToastProvider>
        <ResumeOptimize resumeId="r1" resumeTitle="QA Resume" onOptimized={() => {}} />
      </ToastProvider>,
    )

    expect(screen.getByText('No saved jobs found. Search for jobs first.')).toBeInTheDocument()
  })
})
