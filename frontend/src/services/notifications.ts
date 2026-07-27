export type NotificationChannel = 'browser' | 'email' | 'sms' | 'push' | 'slack'

export interface NotificationPayload {
  title: string
  body: string
  url?: string
  metadata?: Record<string, string>
}

export interface NotificationProvider {
  name: NotificationChannel
  send(payload: NotificationPayload): Promise<boolean>
  isAvailable(): boolean
}

class BrowserNotificationProvider implements NotificationProvider {
  name: NotificationChannel = 'browser'

  isAvailable(): boolean {
    return 'Notification' in window && Notification.permission !== 'denied'
  }

  async send(payload: NotificationPayload): Promise<boolean> {
    if (!this.isAvailable()) {
      if (Notification.permission === 'default') {
        const permission = await Notification.requestPermission()
        if (permission !== 'granted') return false
      } else {
        return false
      }
    }

    try {
      const n = new Notification(payload.title, {
        body: payload.body,
        icon: '/favicon.ico',
      })
      if (payload.url) {
        n.onclick = () => window.open(payload.url, '_self')
      }
      return true
    } catch {
      return false
    }
  }
}

class ConsoleNotificationProvider implements NotificationProvider {
  name: NotificationChannel = 'browser'

  isAvailable(): boolean { return true }

  async send(payload: NotificationPayload): Promise<boolean> {
    console.info(`[Notification] ${payload.title}: ${payload.body}`)
    return true
  }
}

export const notificationService = {
  providers: {
    browser: new BrowserNotificationProvider(),
    console: new ConsoleNotificationProvider(),
  },

  async send(payload: NotificationPayload, channels: NotificationChannel[] = ['browser']): Promise<Record<NotificationChannel, boolean>> {
    const results: Record<NotificationChannel, boolean> = {} as any
    for (const channel of channels) {
      const provider = this.providers[channel as keyof typeof this.providers]
      if (provider) {
        results[channel] = await provider.send(payload)
      }
    }
    return results
  },

  async requestPermission(): Promise<boolean> {
    if (!('Notification' in window)) return false
    if (Notification.permission === 'granted') return true
    if (Notification.permission === 'denied') return false
    const permission = await Notification.requestPermission()
    return permission === 'granted'
  },

  isSupported(): boolean {
    return 'Notification' in window
  },
}
