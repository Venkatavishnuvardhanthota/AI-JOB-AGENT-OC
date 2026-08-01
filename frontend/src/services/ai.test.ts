import { describe, it, expect, vi, beforeEach } from 'vitest'
import { aiService } from './ai'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

const API_BASE = '/api/v1'

function mockResponse(data: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.setItem('access_token', 'test-token')
})

describe('aiService', () => {
  it('listProviders calls GET /ai/providers', async () => {
    mockFetch.mockResolvedValue(mockResponse({ success: true, data: [{ name: 'openrouter' }] }))
    const result = await aiService.listProviders()
    expect(result).toEqual([{ name: 'openrouter' }])
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining(`${API_BASE}/ai/providers`),
      expect.objectContaining({ method: 'GET' }),
    )
  })

  it('getProvider calls GET /ai/providers/:name', async () => {
    mockFetch.mockResolvedValue(mockResponse({ success: true, data: { name: 'openai' } }))
    const result = await aiService.getProvider('openai')
    expect(result).toEqual({ name: 'openai' })
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining(`${API_BASE}/ai/providers/openai`),
      expect.anything(),
    )
  })

  it('testConnection calls POST /ai/providers/:name/test', async () => {
    mockFetch.mockResolvedValue(mockResponse({ success: true, data: { healthy: true, latency_ms: 150 } }))
    const result = await aiService.testConnection('openai')
    expect(result).toEqual({ healthy: true, latency_ms: 150 })
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining(`${API_BASE}/ai/providers/openai/test`),
      expect.objectContaining({ method: 'POST' }),
    )
  })

  it('getModels calls GET /ai/models', async () => {
    mockFetch.mockResolvedValue(mockResponse({ success: true, data: [{ id: 'gpt-4' }] }))
    const result = await aiService.getModels()
    expect(result).toEqual([{ id: 'gpt-4' }])
  })

  it('getModels with provider calls GET /ai/models?provider=...', async () => {
    mockFetch.mockResolvedValue(mockResponse({ success: true, data: [] }))
    await aiService.getModels('openai')
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('?provider=openai'),
      expect.anything(),
    )
  })

  it('getHealth calls GET /ai/health', async () => {
    mockFetch.mockResolvedValue(mockResponse({ success: true, data: { status: 'healthy', overall_healthy: true, providers: [] } }))
    const result = await aiService.getHealth()
    expect(result.status).toBe('healthy')
    expect(result.overall_healthy).toBe(true)
  })

  it('getConfig calls GET /ai/config', async () => {
    mockFetch.mockResolvedValue(mockResponse({ success: true, data: { default_provider: 'openrouter', temperature: 0.7 } }))
    const result = await aiService.getConfig()
    expect(result.default_provider).toBe('openrouter')
    expect(result.temperature).toBe(0.7)
  })

  it('updateConfig calls PUT /ai/config', async () => {
    mockFetch.mockResolvedValue(mockResponse({ success: true, data: { updates: ['temperature'], message: 'ok', note: '' } }))
    const result = await aiService.updateConfig({ temperature: 0.8 })
    expect(result.updates).toEqual(['temperature'])
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining(`${API_BASE}/ai/config`),
      expect.objectContaining({ method: 'PUT' }),
    )
  })

  it('listPrompts calls GET /ai/prompts', async () => {
    mockFetch.mockResolvedValue(mockResponse({ success: true, data: [{ name: 'resume-generation', variables: ['job_title'] }] }))
    const result = await aiService.listPrompts()
    expect(result).toEqual([{ name: 'resume-generation', variables: ['job_title'] }])
  })

  it('throws on non-ok response', async () => {
    mockFetch.mockResolvedValue(mockResponse({ detail: 'Not found' }, 404))
    await expect(aiService.getProvider('nonexistent')).rejects.toThrow()
  })
})
