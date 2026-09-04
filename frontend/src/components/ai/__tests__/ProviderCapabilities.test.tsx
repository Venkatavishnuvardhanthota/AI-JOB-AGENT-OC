import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { ProviderCapabilities } from '../ProviderCapabilities'
import type { CapabilityInfo } from '@/types'

describe('ProviderCapabilities', () => {
  it('renders "No capability info" when capabilities is undefined', () => {
    render(<ProviderCapabilities />)
    expect(screen.getByText('No capability info')).toBeInTheDocument()
  })

  it('renders "Basic only" when no capabilities are enabled', () => {
    const caps: CapabilityInfo = {
      chat: false, streaming: false, vision: false, json_mode: false,
      embeddings: false, reasoning: false, function_calling: false,
      tool_calling: false, system_prompt_support: false, structured_output: false,
    }
    render(<ProviderCapabilities capabilities={caps} />)
    expect(screen.getByText('Basic only')).toBeInTheDocument()
  })

  it('renders badges for enabled capabilities', () => {
    const caps: CapabilityInfo = {
      chat: true, streaming: true, vision: false, json_mode: true,
      embeddings: false, reasoning: false, function_calling: false,
      tool_calling: false, system_prompt_support: true, structured_output: false,
    }
    render(<ProviderCapabilities capabilities={caps} />)
    expect(screen.getByText('Chat')).toBeInTheDocument()
    expect(screen.getByText('Streaming')).toBeInTheDocument()
    expect(screen.getByText('JSON Mode')).toBeInTheDocument()
    expect(screen.getByText('System Prompts')).toBeInTheDocument()
    expect(screen.queryByText('Vision')).not.toBeInTheDocument()
  })
})
