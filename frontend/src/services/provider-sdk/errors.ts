export class ProviderError extends Error {
  constructor(
    message: string,
    public code: string,
    public providerId?: string,
    public recoverable = false
  ) {
    super(message)
    this.name = 'ProviderError'
  }
}

export class AuthenticationError extends ProviderError {
  constructor(message: string, providerId?: string) {
    super(message, 'AUTHENTICATION_ERROR', providerId, false)
    this.name = 'AuthenticationError'
  }
}

export class RateLimitError extends ProviderError {
  constructor(message: string, providerId?: string, public retryAfterMs?: number) {
    super(message, 'RATE_LIMIT_ERROR', providerId, true)
    this.name = 'RateLimitError'
  }
}

export class SessionExpiredError extends ProviderError {
  constructor(message: string, providerId?: string) {
    super(message, 'SESSION_EXPIRED_ERROR', providerId, true)
    this.name = 'SessionExpiredError'
  }
}

export class ProviderUnavailableError extends ProviderError {
  constructor(message: string, providerId?: string) {
    super(message, 'PROVIDER_UNAVAILABLE_ERROR', providerId, true)
    this.name = 'ProviderUnavailableError'
  }
}

export class SearchError extends ProviderError {
  constructor(message: string, providerId?: string) {
    super(message, 'SEARCH_ERROR', providerId, false)
    this.name = 'SearchError'
  }
}

export class ApplicationError extends ProviderError {
  constructor(message: string, providerId?: string) {
    super(message, 'APPLICATION_ERROR', providerId, false)
    this.name = 'ApplicationError'
  }
}

export class ValidationError extends ProviderError {
  constructor(message: string, providerId?: string, public field?: string) {
    super(message, 'VALIDATION_ERROR', providerId, false)
    this.name = 'ValidationError'
  }
}

export class TimeoutError extends ProviderError {
  constructor(message: string, providerId?: string) {
    super(message, 'TIMEOUT_ERROR', providerId, true)
    this.name = 'TimeoutError'
  }
}

export class NotImplementedError extends ProviderError {
  constructor(operation: string, providerId?: string) {
    super(`${operation} is not implemented`, 'NOT_IMPLEMENTED', providerId, false)
    this.name = 'NotImplementedError'
  }
}

export function isProviderError(error: unknown): error is ProviderError {
  return error instanceof ProviderError
}

export function isRecoverableError(error: unknown): boolean {
  return isProviderError(error) && error.recoverable
}

export function getErrorCode(error: unknown): string {
  if (isProviderError(error)) return error.code
  return 'UNKNOWN_ERROR'
}
