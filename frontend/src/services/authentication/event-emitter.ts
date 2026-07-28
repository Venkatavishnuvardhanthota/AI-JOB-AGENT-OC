import type { AuthEventType, AuthEventPayload } from './types'

type EventListener<E extends AuthEventType> = (payload: AuthEventPayload[E]) => void

const listeners = new Map<string, Set<(...args: unknown[]) => void>>()

export const authEventEmitter = {
  on<E extends AuthEventType>(event: E, listener: EventListener<E>): () => void {
    if (!listeners.has(event)) listeners.set(event, new Set())
    listeners.get(event)!.add(listener as (...args: unknown[]) => void)
    return () => { listeners.get(event)?.delete(listener as (...args: unknown[]) => void) }
  },

  off<E extends AuthEventType>(event: E, listener: EventListener<E>): void {
    listeners.get(event)?.delete(listener as (...args: unknown[]) => void)
  },

  emit<E extends AuthEventType>(event: E, payload: AuthEventPayload[E]): void {
    const eventListeners = listeners.get(event)
    if (eventListeners) {
      for (const listener of eventListeners) {
        try { listener(payload) } catch { }
      }
    }
  },

  removeAll(event?: AuthEventType): void {
    if (event) listeners.delete(event)
    else listeners.clear()
  },

  listenerCount(event: AuthEventType): number {
    return listeners.get(event)?.size ?? 0
  },
}
