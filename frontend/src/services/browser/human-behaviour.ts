import type { HumanBehaviourConfig } from './types'
import { DEFAULT_HUMAN_CONFIG } from './types'
import { randomBetween } from './utils'

export const humanBehaviourService = {
  config: { ...DEFAULT_HUMAN_CONFIG },

  updateConfig(updates: Partial<HumanBehaviourConfig>): void {
    this.config = { ...this.config, ...updates }
  },

  resetConfig(): void {
    this.config = { ...DEFAULT_HUMAN_CONFIG }
  },

  getTypingDelay(): number {
    return randomBetween(this.config.typingSpeed.min, this.config.typingSpeed.max)
  },

  getMouseDelay(): number {
    return randomBetween(this.config.mouseSpeed.min, this.config.mouseSpeed.max)
  },

  getActionPause(): number {
    return randomBetween(this.config.pauseBetweenActions.min, this.config.pauseBetweenActions.max)
  },

  getScrollSpeed(): number {
    return randomBetween(this.config.scrollSpeed.min, this.config.scrollSpeed.max)
  },

  randomizeTyping(text: string): string {
    if (!this.config.randomMistakes) return text
    const chars = text.split('')
    for (let i = 0; i < chars.length; i++) {
      if (Math.random() < 0.02) {
        chars[i] = String.fromCharCode(chars[i].charCodeAt(0) + (Math.random() > 0.5 ? 1 : -1))
      }
    }
    return chars.join('')
  },

  shouldSimulateError(): boolean {
    return this.config.enabled && Math.random() < this.config.errorRate
  },

  async humanType(
    text: string,
    onChar: (char: string) => void
  ): Promise<void> {
    if (!this.config.enabled) {
      text.split('').forEach(c => onChar(c))
      return
    }
    const randomized = this.randomizeTyping(text)
    for (const char of randomized) {
      onChar(char)
      await this.delay(this.getTypingDelay())
    }
  },

  async humanMove(
    _fromX: number, _fromY: number, _toX: number, _toY: number,
    onMove: (x: number, y: number) => void
  ): Promise<void> {
    if (!this.config.enabled) {
      onMove(0, 0)
      return
    }
    const steps = randomBetween(5, 15)
    for (let i = 0; i <= steps; i++) {
      const t = i / steps
      const x = this.bezierCurve(t, 0, 10, -10, 0) * 5
      const y = this.bezierCurve(t, 0, 5, -5, 0) * 5
      onMove(Math.round(x), Math.round(y))
      await this.delay(this.getMouseDelay())
    }
  },

  async humanScroll(
    targetY: number,
    onScroll: (y: number) => void
  ): Promise<void> {
    if (!this.config.enabled) {
      onScroll(targetY)
      return
    }
    const steps = randomBetween(3, 8)
    for (let i = 1; i <= steps; i++) {
      const y = Math.round((targetY / steps) * i)
      onScroll(y)
      await this.delay(this.getScrollSpeed())
    }
  },

  async delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  },

  bezierCurve(t: number, p0: number, p1: number, p2: number, p3: number): number {
    const u = 1 - t
    return u * u * u * p0 + 3 * u * u * t * p1 + 3 * u * t * t * p2 + t * t * t * p3
  },
}
