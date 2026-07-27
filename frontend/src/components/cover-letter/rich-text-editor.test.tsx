import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { RichTextEditor } from './rich-text-editor'

describe('RichTextEditor', () => {
  it('renders with placeholder text', () => {
    const onChange = vi.fn()
    render(<RichTextEditor value="" onChange={onChange} placeholder="Start writing..." />)
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('renders with content', () => {
    const onChange = vi.fn()
    render(<RichTextEditor value="<p>Hello World</p>" onChange={onChange} />)
    expect(screen.getByText(/hello world/i)).toBeInTheDocument()
  })

  it('shows word count', () => {
    const onChange = vi.fn()
    render(<RichTextEditor value="<p>Two words</p>" onChange={onChange} />)
    expect(screen.getByText('2 words')).toBeInTheDocument()
  })

  it('shows character count', () => {
    const onChange = vi.fn()
    render(<RichTextEditor value="<p>Hello</p>" onChange={onChange} />)
    expect(screen.getByText('5 characters')).toBeInTheDocument()
  })

  it('shows reading time', () => {
    const onChange = vi.fn()
    const longText = '<p>' + Array(200).fill('word').join(' ') + '</p>'
    render(<RichTextEditor value={longText} onChange={onChange} />)
    expect(screen.getByText('1 min read')).toBeInTheDocument()
  })

  it('toggles preview mode', () => {
    const onChange = vi.fn()
    render(<RichTextEditor value="<p>Content</p>" onChange={onChange} />)
    fireEvent.click(screen.getByLabelText('Print preview'))
    expect(screen.getByText('Edit')).toBeInTheDocument()
  })

  it('renders toolbar buttons', () => {
    const onChange = vi.fn()
    render(<RichTextEditor value="" onChange={onChange} />)
    expect(screen.getByLabelText('Bold (Ctrl+B)')).toBeInTheDocument()
    expect(screen.getByLabelText('Italic (Ctrl+I)')).toBeInTheDocument()
    expect(screen.getByLabelText('Underline (Ctrl+U)')).toBeInTheDocument()
  })
})
