import { useEffect } from 'react'

interface Shortcut {
  key: string
  ctrl?: boolean
  shift?: boolean
  handler: (e: KeyboardEvent) => void
  enabled?: boolean
  ignoreWhenFocused?: boolean
}

const FOCUSABLE_SELECTORS = 'input, textarea, select, [contenteditable]'

export function useKeyboardShortcuts(shortcuts: Shortcut[]) {
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      for (const s of shortcuts) {
        if (s.enabled === false) continue

        const keyMatch = e.key.toLowerCase() === s.key.toLowerCase()
        const ctrlMatch = !!s.ctrl === (e.ctrlKey || e.metaKey)
        const shiftMatch = !!s.shift === e.shiftKey

        if (!keyMatch || !ctrlMatch || !shiftMatch) continue

        if (s.ignoreWhenFocused !== false) {
          const target = e.target as HTMLElement
          if (target && target.closest(FOCUSABLE_SELECTORS)) continue
        }

        e.preventDefault()
        s.handler(e)
        return
      }
    }

    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [shortcuts])
}
