import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ExportPreviewModal } from './export-preview-modal'

describe('ExportPreviewModal', () => {
  it('renders when open', () => {
    render(
      <ExportPreviewModal
        open={true}
        onClose={vi.fn()}
        content="<p>Test Content</p>"
        title="My Letter"
        onExport={vi.fn()}
      />,
    )
    expect(screen.getByText(/export preview/i)).toBeInTheDocument()
    expect(screen.getByText(/my letter/i)).toBeInTheDocument()
  })

  it('does not render when closed', () => {
    render(
      <ExportPreviewModal
        open={false}
        onClose={vi.fn()}
        content="<p>Test Content</p>"
        title="My Letter"
        onExport={vi.fn()}
      />,
    )
    expect(screen.queryByText(/export preview/i)).not.toBeInTheDocument()
  })

  it('renders export buttons', () => {
    render(
      <ExportPreviewModal
        open={true}
        onClose={vi.fn()}
        content="<p>Content</p>"
        title="Letter"
        onExport={vi.fn()}
      />,
    )
    expect(screen.getByText(/export pdf/i)).toBeInTheDocument()
    expect(screen.getByText(/export docx/i)).toBeInTheDocument()
  })

  it('calls onClose when close is clicked', () => {
    const onClose = vi.fn()
    render(
      <ExportPreviewModal
        open={true}
        onClose={onClose}
        content="<p>Content</p>"
        title="Letter"
        onExport={vi.fn()}
      />,
    )
    fireEvent.click(screen.getByText('Close'))
    expect(onClose).toHaveBeenCalled()
  })
})
