export const v4Service = {
  generate(prefix: string = 'id'): string {
    const timestamp = Date.now().toString(36)
    const random = Math.random().toString(36).slice(2, 10)
    return `${prefix}_${timestamp}_${random}`
  },
}

export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

export function computeBackoffDelay(base: number, max: number, factor: number, attempt: number): number {
  return Math.min(base * Math.pow(factor, attempt - 1), max)
}

export function nowISO(): string {
  return new Date().toISOString()
}
