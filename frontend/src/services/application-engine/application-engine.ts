import type { ProviderId } from '../discovery/types'
import type { ProfileData, ProfileEducation, ProfileExperience, ProfileProject, ProfileCertification, ProfileLanguage, FormEngineConfig } from './types'
import { FormEngine } from './form-engine'
import { profileMapper } from './profile-mapper'

export class ApplicationEngine {
  private engines: Map<string, FormEngine> = new Map()
  private profile: ProfileData | null = null

  setProfile(
    profile: Partial<ProfileData>,
    education?: ProfileEducation[],
    experience?: ProfileExperience[],
    projects?: ProfileProject[],
    skills?: string[],
    certifications?: ProfileCertification[],
    languages?: ProfileLanguage[]
  ): void {
    this.profile = profileMapper.buildProfile(profile, education, experience, projects, skills, certifications, languages)
  }

  getProfile(): ProfileData | null {
    return this.profile
  }

  createEngine(engineId: string, config?: Partial<FormEngineConfig>): FormEngine {
    const engine = new FormEngine(config)
    if (this.profile) {
      engine.setProfile(this.profile)
    }
    this.engines.set(engineId, engine)
    return engine
  }

  getEngine(engineId: string): FormEngine | undefined {
    return this.engines.get(engineId)
  }

  removeEngine(engineId: string): boolean {
    return this.engines.delete(engineId)
  }

  listEngines(): string[] {
    return Array.from(this.engines.keys())
  }

  async submitApplication(
    engineId: string,
    sessionId: string,
    providerId: ProviderId,
    applicationUrl: string
  ) {
    const engine = this.engines.get(engineId)
    if (!engine) throw new Error(`Engine not found: ${engineId}`)

    if (!engine.getForm()) {
      await engine.detectForm(applicationUrl, sessionId)
    }

    if (this.profile) engine.setProfile(this.profile)
    engine.mapFields()
    await engine.fillFields(sessionId, engineId)
    engine.validate()
    await engine.review()
    return await engine.submit(sessionId, providerId, applicationUrl)
  }

  resetAll(): void {
    for (const engine of this.engines.values()) {
      engine.reset()
    }
    this.engines.clear()
    this.profile = null
  }
}
