import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect } from 'vitest'
import App from './App'

describe('App', () => {
  it('renders the login page by default', () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>,
    )
    expect(
      screen.getByRole('heading', { name: /welcome back/i }),
    ).toBeInTheDocument()
  })
})
