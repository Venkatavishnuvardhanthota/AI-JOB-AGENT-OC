import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect } from 'vitest'
import { ErrorPage } from './ErrorPage'

describe('ErrorPage', () => {
  it('renders generic error by default', () => {
    render(
      <MemoryRouter initialEntries={['/error']}>
        <ErrorPage />
      </MemoryRouter>,
    )
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('renders 500 error with code param', () => {
    render(
      <MemoryRouter initialEntries={['/error?code=500']}>
        <ErrorPage />
      </MemoryRouter>,
    )
    expect(screen.getByText('Server error')).toBeInTheDocument()
  })

  it('renders offline error', () => {
    render(
      <MemoryRouter initialEntries={['/error?code=offline']}>
        <ErrorPage />
      </MemoryRouter>,
    )
    expect(screen.getByText("You're offline")).toBeInTheDocument()
  })

  it('renders permission error', () => {
    render(
      <MemoryRouter initialEntries={['/error?code=permission']}>
        <ErrorPage />
      </MemoryRouter>,
    )
    expect(screen.getByText('Permission denied')).toBeInTheDocument()
  })
})
