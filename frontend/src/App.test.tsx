import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect } from 'vitest'
import App from './App'

describe('App', () => {
  it('renders the application title', () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>,
    )
    expect(
      screen.getByText('AI Job Application Agent'),
    ).toBeInTheDocument()
  })
})
