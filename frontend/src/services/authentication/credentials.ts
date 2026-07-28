import { ValidationError } from './types'

export class CredentialBundle {
  private readonly data: Map<string, unknown> = new Map()
  private sealed = false

  constructor(initial?: Record<string, unknown>) {
    if (initial) {
      for (const [key, value] of Object.entries(initial)) {
        this.data.set(key, value)
      }
    }
  }

  set(key: string, value: unknown): void {
    if (this.sealed) throw new Error('CredentialBundle is sealed')
    this.data.set(key, value)
  }

  get(key: string): unknown {
    return this.data.get(key)
  }

  getString(key: string): string | undefined {
    const val = this.data.get(key)
    return typeof val === 'string' ? val : undefined
  }

  has(key: string): boolean {
    return this.data.has(key)
  }

  seal(): void {
    this.sealed = true
  }

  get isSealed(): boolean {
    return this.sealed
  }

  get username(): string | undefined {
    return this.getString('username')
  }

  get password(): string | undefined {
    return this.getString('password')
  }

  get token(): string | undefined {
    return this.getString('token')
  }

  get apiKey(): string | undefined {
    return this.getString('apiKey')
  }

  get clientId(): string | undefined {
    return this.getString('clientId')
  }

  get clientSecret(): string | undefined {
    return this.getString('clientSecret')
  }

  get refreshToken(): string | undefined {
    return this.getString('refreshToken')
  }

  get sessionCookie(): string | undefined {
    return this.getString('sessionCookie')
  }

  toRecord(): Record<string, unknown> {
    const result: Record<string, unknown> = {}
    for (const [key, value] of this.data) {
      if (key !== 'password' && key !== 'clientSecret' && key !== 'token') {
        result[key] = value
      }
    }
    return result
  }

  toSecureRecord(): Record<string, unknown> {
    const result: Record<string, unknown> = {}
    for (const [key, value] of this.data) {
      result[key] = value
    }
    return result
  }

  static fromUsernamePassword(username: string, password: string): CredentialBundle {
    return new CredentialBundle({ username, password })
  }

  static fromToken(token: string): CredentialBundle {
    return new CredentialBundle({ token })
  }

  static fromApiKey(apiKey: string): CredentialBundle {
    return new CredentialBundle({ apiKey })
  }

  static fromOAuth(clientId: string, clientSecret: string, refreshToken?: string): CredentialBundle {
    return new CredentialBundle({ clientId, clientSecret, refreshToken })
  }

  static fromCookie(sessionCookie: string): CredentialBundle {
    return new CredentialBundle({ sessionCookie })
  }

  validateRequired(fields: string[]): ValidationError[] {
    const errors: ValidationError[] = []
    for (const field of fields) {
      if (!this.has(field) || this.get(field) === undefined || this.get(field) === '') {
        errors.push({ field, message: `${field} is required`, code: 'MISSING_CREDENTIAL' })
      }
    }
    return errors
  }
}
