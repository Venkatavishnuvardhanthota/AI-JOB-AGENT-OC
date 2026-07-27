import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ToastProvider } from '@/components/ui/toast'
import { TemplatePanel } from './template-panel'

function renderWithToast(ui: React.ReactElement) {
  return render(<ToastProvider>{ui}</ToastProvider>)
}

describe('TemplatePanel', () => {
  it('renders all templates', () => {
    const onSelect = vi.fn()
    renderWithToast(<TemplatePanel currentTemplate="modern" onSelect={onSelect} />)

    expect(screen.getByText('Modern')).toBeInTheDocument()
    expect(screen.getByText('Classic')).toBeInTheDocument()
    expect(screen.getByText('Executive')).toBeInTheDocument()
    expect(screen.getByText('Technical')).toBeInTheDocument()
    expect(screen.getByText('Minimal')).toBeInTheDocument()
    expect(screen.getByText('Graduate')).toBeInTheDocument()
  })

  it('calls onSelect when template is clicked', () => {
    const onSelect = vi.fn()
    renderWithToast(<TemplatePanel currentTemplate="modern" onSelect={onSelect} />)

    fireEvent.click(screen.getByLabelText('Select Classic template'))
    expect(onSelect).toHaveBeenCalledWith('classic')
  })

  it('shows description text', () => {
    const onSelect = vi.fn()
    renderWithToast(<TemplatePanel currentTemplate="modern" onSelect={onSelect} />)

    expect(screen.getByText(/preserves your content/i)).toBeInTheDocument()
  })
})
