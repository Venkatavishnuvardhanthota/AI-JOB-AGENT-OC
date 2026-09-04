import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ToastProvider } from '@/components/ui/toast'
import { ResumeUpload } from './resume-upload'

const hooksMock = vi.hoisted(() => ({
  useUploadResume: vi.fn(),
}))

vi.mock('@/api/hooks', () => hooksMock)

function makeFile() {
  return new File(['%PDF-1.4 fake'], 'resume.pdf', { type: 'application/pdf' })
}

describe('ResumeUpload', () => {
  let mutateAsync: ReturnType<typeof vi.fn>
  let onComplete: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mutateAsync = vi.fn()
    onComplete = vi.fn()
    hooksMock.useUploadResume.mockReturnValue({ mutateAsync })
  })

  it('calls onComplete with the full upload result, not a top-level id', async () => {
    const uploadResult = {
      resume: { id: 'up1', title: 'Jane Austen Resume', sections: [{ section_type: 'summary', title: 'Summary' }] },
      confidence: 92,
      needs_review: [],
    }
    mutateAsync.mockResolvedValue(uploadResult)

    render(
      <ToastProvider>
        <ResumeUpload onComplete={onComplete} />
      </ToastProvider>,
    )

    const input = screen.getByLabelText('Upload resume file').querySelector('input[type=file]') as HTMLInputElement
    fireEvent.change(input, { target: { files: [makeFile()] } })
    fireEvent.click(screen.getByRole('button', { name: /Upload/ }))

    await waitFor(() => expect(onComplete).toHaveBeenCalledTimes(1), { timeout: 3000 })
    expect(onComplete).toHaveBeenCalledWith(uploadResult)
    expect(onComplete.mock.calls[0][0]?.resume?.id).toBe('up1')
    expect(onComplete.mock.calls[0][0]?.resume).toBeTruthy()
  })
})
