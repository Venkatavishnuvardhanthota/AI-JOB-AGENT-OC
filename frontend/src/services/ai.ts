import { api } from '@/api/client'
import type {
  AIProvider,
  AIHealthResponse,
  AIConfigData,
  AIUpdateConfigData,
  AIModel,
  AIProviderTestResult,
  PromptTemplateInfo,
  ResumeStrategySettingsData,
  ResumeStrategySettingsUpdateData,
  ResumeStrategyPreviewData,
  ResumeStrategyPrepareData,
  APISuccessResponse,
} from '@/types'

function unwrap<T>(res: APISuccessResponse<T>): T {
  return res.data
}

export const aiService = {
  listProviders(): Promise<AIProvider[]> {
    return api.get<APISuccessResponse<AIProvider[]>>('/ai/providers').then(unwrap)
  },

  getProvider(provider: string): Promise<AIProvider> {
    return api.get<APISuccessResponse<AIProvider>>(`/ai/providers/${provider}`).then(unwrap)
  },

  testConnection(provider: string): Promise<AIProviderTestResult> {
    return api.post<APISuccessResponse<AIProviderTestResult>>(`/ai/providers/${provider}/test`).then(unwrap)
  },

  getModels(provider?: string): Promise<AIModel[]> {
    const q = provider ? `?provider=${provider}` : ''
    return api.get<APISuccessResponse<AIModel[]>>(`/ai/models${q}`).then(unwrap)
  },

  getHealth(): Promise<AIHealthResponse> {
    return api.get<APISuccessResponse<AIHealthResponse>>('/ai/health').then(unwrap)
  },

  getConfig(): Promise<AIConfigData> {
    return api.get<APISuccessResponse<AIConfigData>>('/ai/config').then(unwrap)
  },

  updateConfig(data: AIUpdateConfigData): Promise<{ updates: string[]; message: string; note: string }> {
    return api.put<APISuccessResponse<{ updates: string[]; message: string; note: string }>>('/ai/config', data).then(unwrap)
  },

  listPrompts(): Promise<PromptTemplateInfo[]> {
    return api.get<APISuccessResponse<PromptTemplateInfo[]>>('/ai/prompts').then(unwrap)
  },

  getResumeStrategy(): Promise<ResumeStrategySettingsData> {
    return api.get<APISuccessResponse<ResumeStrategySettingsData>>('/ai/settings/resume-strategy').then(unwrap)
  },

  updateResumeStrategy(data: ResumeStrategySettingsUpdateData): Promise<ResumeStrategySettingsData> {
    return api.put<APISuccessResponse<ResumeStrategySettingsData>>('/ai/settings/resume-strategy', data).then(unwrap)
  },

  previewResumeStrategy(jobId: string): Promise<ResumeStrategyPreviewData> {
    return api.post<APISuccessResponse<ResumeStrategyPreviewData>>('/ai/strategy/preview', { job_id: jobId }).then(unwrap)
  },

  selectResumeStrategy(data: {
    job_id: string
    strategy_override?: ResumeStrategySettingsData['resume_strategy']
    resume_id?: string
    generate_cover_letter?: boolean
  }): Promise<ResumeStrategyPrepareData> {
    return api.post<APISuccessResponse<ResumeStrategyPrepareData>>('/ai/strategy/select', data).then(unwrap)
  },
}
