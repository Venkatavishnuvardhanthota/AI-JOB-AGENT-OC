export const v4Service = {
  generate(prefix: string = 'id'): string {
    const timestamp = Date.now().toString(36)
    const random = Math.random().toString(36).slice(2, 10)
    return `${prefix}_${timestamp}_${random}`
  },
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

export function randomBetween(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

export function cosineSimilarity(a: string[], b: string[]): number {
  if (a.length === 0 || b.length === 0) return 0
  const setA = new Set(a.map(s => s.toLowerCase()))
  const setB = new Set(b.map(s => s.toLowerCase()))
  let intersection = 0
  for (const item of setA) {
    if (setB.has(item)) intersection++
  }
  const denom = Math.sqrt(setA.size) * Math.sqrt(setB.size)
  return denom === 0 ? 0 : intersection / denom
}

export function calculateOverlap(a: string[], b: string[]): number {
  if (a.length === 0) return 0
  const setB = new Set(b.map(s => s.toLowerCase()))
  const matched = a.filter(s => setB.has(s.toLowerCase()))
  return matched.length / a.length
}

export function truncate(str: string, max: number): string {
  return str.length > max ? str.slice(0, max) + '...' : str
}
