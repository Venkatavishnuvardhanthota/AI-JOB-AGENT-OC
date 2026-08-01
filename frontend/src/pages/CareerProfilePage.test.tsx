import { render, screen, within, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ToastProvider } from '@/components/ui/toast'
import { CareerProfilePage } from './CareerProfilePage'

const clientMock = vi.hoisted(() => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
  jobsApi: {},
  matchingApi: {},
}))

vi.mock('@/api/client', () => clientMock)

let stores: Record<string, any[]>

function setupStores() {
  stores = {
    education: [],
    experience: [],
    projects: [],
    skills: [],
    certifications: [],
    languages: [],
    'social-links': [],
    achievements: [],
  }
  const api = clientMock.api

  api.get.mockImplementation(async (endpoint: string) => {
    if (endpoint === '/profile') {
      return {
        success: true,
        data: {
          id: 'p1', headline: 'Senior Dev', professional_summary: 'Loves python.',
          current_role: null, desired_role: null, employment_status: null,
          total_years_experience: null, notice_period: null, current_salary: null,
          expected_salary: null, salary_preference: null, willing_to_relocate: null,
          visa_sponsorship_requirement: null, portfolio_url: null, linkedin_url: null,
          github_url: null, website_url: null, profile_completeness: 0,
          education: [], experience: [], projects: [], skills: [], certifications: [],
          languages: [], social_links: [], achievements: [], preferences: null,
          created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z',
        },
      }
    }
    if (endpoint === '/profile/completeness') {
      return { success: true, data: { percentage: 0, breakdown: {}, missing_sections: [] } }
    }
    const match = endpoint.match(/^\/profile\/([a-z-]+)$/)
    if (match && match[1] in stores) return { success: true, data: stores[match[1]] }
    throw new Error(`Unexpected GET ${endpoint}`)
  })

  api.post.mockImplementation(async (endpoint: string, body: any = {}) => {
    const match = endpoint.match(/^\/profile\/([a-z-]+)$/)
    if (match && match[1] in stores) {
      const list = stores[match[1]]
      if (endpoint === '/profile/social-links') {
        const platform = String(body.platform || '').toLowerCase().replace(' ', '')
        if (list.some(item => item.platform === platform)) {
          throw new Error(`Duplicate social link. '${platform}' is already linked in your profile.`)
        }
        const item = { id: `link-${list.length + 1}`, ...body, platform, title: 'GitHub' }
        list.push(item)
        return { success: true, data: item }
      }
      const item = { id: `id-${list.length + 1}`, ...body }
      list.push(item)
      return { success: true, data: item }
    }
    throw new Error(`Unexpected POST ${endpoint}`)
  })

  api.patch.mockImplementation(async (endpoint: string, body: any = {}) => {
    const match = endpoint.match(/^\/profile\/([a-z-]+)\/(.+)$/)
    if (match && match[1] in stores) {
      const item = stores[match[1]].find(entry => entry.id === match[2])
      if (item) Object.assign(item, body)
      return { success: true, data: item || {} }
    }
    throw new Error(`Unexpected PATCH ${endpoint}`)
  })

  api.put.mockImplementation(async (endpoint: string, body: any = {}) => {
    if (endpoint === '/profile/skills') {
      stores.skills = body.skills.map((name: string, i: number) => ({ id: `skill-${i + 1}`, name }))
      return { success: true, data: stores.skills }
    }
    throw new Error(`Unexpected PUT ${endpoint}`)
  })

  api.delete.mockImplementation(async (endpoint: string) => {
    const match = endpoint.match(/^\/profile\/([a-z-]+)\/(.+)$/)
    if (match && match[1] in stores) {
      stores[match[1]] = stores[match[1]].filter(item => item.id !== match[2])
      return undefined
    }
    throw new Error(`Unexpected DELETE ${endpoint}`)
  })
}

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <MemoryRouter>
          <CareerProfilePage />
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  )
}

async function openModal(ctaName: string) {
  const cta = await screen.findByRole('button', { name: ctaName })
  fireEvent.click(cta)
  return screen.findByRole('dialog')
}

beforeEach(() => {
  setupStores()
  vi.spyOn(window, 'confirm').mockReturnValue(true)
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('CareerProfilePage - Social Links', () => {
  it('refreshes the list immediately after adding a link', async () => {
    renderPage()
    const dialog = await openModal('Add link')

    fireEvent.change(within(dialog).getByLabelText(/Platform/), { target: { value: 'github' } })
    fireEvent.change(within(dialog).getByLabelText(/URL/), { target: { value: 'https://github.com/test' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Add' }))

    expect(await screen.findByRole('button', { name: 'Delete GitHub' })).toBeInTheDocument()
    expect(screen.queryByText('No social links added yet.')).not.toBeInTheDocument()
    expect(stores['social-links']).toHaveLength(1)
  })

  it('refreshes the list immediately after editing and deleting', async () => {
    stores['social-links'] = [{ id: 'link-1', platform: 'github', url: 'https://github.com/test', title: 'GitHub' }]
    renderPage()

    expect(await screen.findByText('GitHub')).toBeInTheDocument()

    const card = (await screen.findByRole('heading', { name: /Social Links/ })).closest('.rounded-xl') as HTMLElement
    fireEvent.click(within(card).getByRole('button', { name: 'Edit GitHub' }))
    const dialog = await screen.findByRole('dialog')
    fireEvent.change(within(dialog).getByLabelText(/URL/), { target: { value: 'https://github.com/updated' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Update' }))

    expect(await screen.findByRole('button', { name: 'Delete GitHub' })).toBeInTheDocument()
    expect(stores['social-links'][0].url).toBe('https://github.com/updated')

    fireEvent.click(screen.getByRole('button', { name: 'Delete GitHub' }))

    expect(await screen.findByText('No social links added yet.')).toBeInTheDocument()
    expect(stores['social-links']).toHaveLength(0)
  })

  it('shows a user-friendly message on duplicate platform (409)', async () => {
    stores['social-links'] = [{ id: 'link-1', platform: 'github', url: 'https://github.com/test', title: 'GitHub' }]
    renderPage()

    const card = (await screen.findByRole('heading', { name: /Social Links/ })).closest('.rounded-xl') as HTMLElement
    fireEvent.click(within(card).getByRole('button', { name: 'Add' }))
    const dialog = await screen.findByRole('dialog')

    fireEvent.change(within(dialog).getByLabelText(/Platform/), { target: { value: 'github' } })
    fireEvent.change(within(dialog).getByLabelText(/URL/), { target: { value: 'https://github.com/other' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Add' }))

    expect(await within(dialog).findByText(/already linked in your profile/)).toBeInTheDocument()
    expect(screen.queryByText(/HTTP 409/)).not.toBeInTheDocument()
    expect(stores['social-links']).toHaveLength(1)
  })
})

describe('CareerProfilePage - Achievements', () => {
  it('offers all expected achievement types in the dropdown', async () => {
    renderPage()
    const dialog = await openModal('Add achievement')
    const options = within(dialog).getAllByRole('option').map(option => option.textContent)
    for (const expected of [
      'Award', 'Certificate', 'Badge', 'Certification', 'Competition', 'Hackathon',
      'Scholarship', 'Publication', 'Patent', 'Research', 'Open Source',
      'Employee Recognition', 'Leadership', 'Volunteer', 'Other',
    ]) {
      expect(options).toContain(expected)
    }
  })

  it('shows a custom label input when Other is selected and submits the custom type', async () => {
    renderPage()
    const dialog = await openModal('Add achievement')

    fireEvent.change(within(dialog).getByLabelText(/Type/), { target: { value: 'Other' } })
    const custom = within(dialog).getByPlaceholderText('Enter custom type')
    fireEvent.change(custom, { target: { value: 'Best Reviewer' } })
    fireEvent.change(within(dialog).getByLabelText(/Title/), { target: { value: 'Won award' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Add' }))

    await waitFor(() => {
      expect(clientMock.api.post).toHaveBeenCalledWith(
        '/profile/achievements',
        expect.objectContaining({ title: 'Won award', achievement_type: 'Best Reviewer' }),
      )
    })
  })

  it('requires a custom label when Other is selected', async () => {
    renderPage()
    const dialog = await openModal('Add achievement')

    fireEvent.change(within(dialog).getByLabelText(/Type/), { target: { value: 'Other' } })
    fireEvent.change(within(dialog).getByLabelText(/Title/), { target: { value: 'Won award' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Add' }))

    expect(await within(dialog).findByText('Please enter a custom type.')).toBeInTheDocument()
    expect(clientMock.api.post).not.toHaveBeenCalled()
  })

  it('prefills the custom type when editing an achievement with a non-preset type', async () => {
    stores.achievements = [{ id: 'ach-1', title: 'Won X', organization: 'Org', achievement_type: "President's Award" }]
    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Edit Won X' }))
    const dialog = await screen.findByRole('dialog')

    const select = within(dialog).getByLabelText('Type') as HTMLSelectElement
    expect(select.value).toBe('Other')
    expect(within(dialog).getByPlaceholderText('Enter custom type')).toHaveValue("President's Award")
  })
})

describe('CareerProfilePage - Skills', () => {
  it('renders saved skills as tags and does not show removed fields', async () => {
    stores.skills = [{ id: 'skill-1', name: 'Python' }]
    renderPage()

    expect(await screen.findByText('Python')).toBeInTheDocument()
    expect(screen.queryByLabelText('Proficiency')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Category')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Skill Level')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Years of Experience')).not.toBeInTheDocument()
  })

  it('adds multiple skills in one interaction and saves the complete list', async () => {
    renderPage()

    const input = await screen.findByLabelText('Add skill')
    fireEvent.change(input, { target: { value: 'Python' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    fireEvent.change(input, { target: { value: 'FastAPI' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    expect(screen.getByText('Python')).toBeInTheDocument()
    expect(screen.getByText('FastAPI')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Save skills' }))

    await waitFor(() => {
      expect(clientMock.api.put).toHaveBeenCalledWith('/profile/skills', { skills: ['Python', 'FastAPI'] })
    })
    expect(await screen.findByText('Saved 2 skills')).toBeInTheDocument()
    expect(stores.skills.map(s => s.name)).toEqual(['Python', 'FastAPI'])
  })

  it('supports comma-separated entry in one interaction', async () => {
    renderPage()

    const input = await screen.findByLabelText('Add skill')
    fireEvent.change(input, { target: { value: 'Go, Rust' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    expect(screen.getByText('Go')).toBeInTheDocument()
    expect(screen.getByText('Rust')).toBeInTheDocument()
  })

  it('prevents duplicates case-insensitively', async () => {
    renderPage()

    const input = await screen.findByLabelText('Add skill')
    fireEvent.change(input, { target: { value: 'Python' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    fireEvent.change(input, { target: { value: 'python' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    expect(await screen.findByRole('alert')).toHaveTextContent('"python" is already in your skills.')
    const chips = within(screen.getByLabelText('Selected skills')).getAllByText('Python')
    expect(chips.length).toBe(1)
  })

  it('refreshes the saved list after a successful save', async () => {
    stores.skills = [{ id: 'skill-1', name: 'Python' }]
    renderPage()

    const input = await screen.findByLabelText('Add skill')
    fireEvent.change(input, { target: { value: 'Docker' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    fireEvent.click(screen.getByRole('button', { name: 'Save skills' }))

    expect(await screen.findByText('Saved 2 skills')).toBeInTheDocument()
    expect(screen.getByText('Docker')).toBeInTheDocument()
  })

  it('removes a tag when its remove button is clicked', async () => {
    stores.skills = [
      { id: 'skill-1', name: 'Python' },
      { id: 'skill-2', name: 'Docker' },
    ]
    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Remove Python' }))
    expect(screen.getByRole('button', { name: 'Save skills' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Save skills' }))

    await waitFor(() => {
      expect(clientMock.api.put).toHaveBeenCalledWith('/profile/skills', { skills: ['Docker'] })
    })
  })
})
