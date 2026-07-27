import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi } from 'vitest'

vi.mock('../context/AuthContext')

import { useAuth } from '../context/AuthContext'
import { GuestRoute } from './GuestRoute'

describe('GuestRoute', () => {
  it('renders children when not authenticated', () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
    } as ReturnType<typeof useAuth>)

    render(
      <MemoryRouter>
        <GuestRoute><div>Guest Content</div></GuestRoute>
      </MemoryRouter>,
    )

    expect(screen.getByText('Guest Content')).toBeInTheDocument()
  })

  it('shows loading when loading', () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: false,
      isLoading: true,
      user: null,
    } as ReturnType<typeof useAuth>)

    render(
      <MemoryRouter>
        <GuestRoute><div>Guest Content</div></GuestRoute>
      </MemoryRouter>,
    )

    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })
})
