import { useCallback, useEffect, useRef, useState } from 'react'

export type SaveStatus = 'saved' | 'saving' | 'unsaved' | 'error'

interface UseAutosaveOptions {
  delay?: number
  onSave: (content: string) => Promise<void>
}

export function useAutosave({ delay = 2000, onSave }: UseAutosaveOptions) {
  const [status, setStatus] = useState<SaveStatus>('saved')
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pendingRef = useRef<string | null>(null)
  const mountedRef = useRef(true)
  const savingRef = useRef(false)

  useEffect(() => { mountedRef.current = true; return () => { mountedRef.current = false } }, [])

  const flush = useCallback(async () => {
    const content = pendingRef.current
    if (content === null || savingRef.current) return
    savingRef.current = true
    pendingRef.current = null
    setStatus('saving')
    try {
      await onSave(content)
      if (mountedRef.current) setStatus('saved')
    } catch {
      if (mountedRef.current) setStatus('error')
    } finally {
      savingRef.current = false
    }
  }, [onSave])

  const onChange = useCallback((content: string) => {
    pendingRef.current = content
    if (status !== 'error') setStatus('unsaved')
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(flush, delay)
  }, [delay, flush, status])

  const saveNow = useCallback(async () => {
    if (timerRef.current) clearTimeout(timerRef.current)
    await flush()
  }, [flush])

  useEffect(() => {
    return () => { if (timerRef.current) clearTimeout(timerRef.current) }
  }, [])

  return { status, onChange, saveNow }
}
