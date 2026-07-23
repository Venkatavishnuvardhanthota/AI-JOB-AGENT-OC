import * as React from "react"
import { cn } from "@/lib/utils"

interface ToastProps {
  message: string
  type: 'success' | 'error' | 'info'
  onClose: () => void
}

export function Toast({ message, type, onClose }: ToastProps) {
  React.useEffect(() => {
    const timer = setTimeout(onClose, 3500)
    return () => clearTimeout(timer)
  }, [onClose])

  return (
    <div
      className={cn(
        "fixed bottom-4 right-4 z-50 flex items-center gap-2 rounded-lg px-4 py-3 shadow-lg animate-in slide-in-from-right",
        type === 'success' && 'bg-success/20 text-success border border-success/30',
        type === 'error' && 'bg-error/20 text-error border border-error/30',
        type === 'info' && 'bg-primary/20 text-primary border border-primary/30'
      )}
    >
      <span>{type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span>
      <span className="text-sm">{message}</span>
      <button className="ml-2 opacity-70 hover:opacity-100" onClick={onClose}>×</button>
    </div>
  )
}

interface ToastContextType {
  addToast: (message: string, type: 'success' | 'error' | 'info') => void
}

const ToastContext = React.createContext<ToastContextType | null>(null)

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<{ id: number; message: string; type: 'success' | 'error' | 'info' }[]>([])
  const nextId = React.useRef(0)

  const addToast = React.useCallback((message: string, type: 'success' | 'error' | 'info') => {
    const id = nextId.current++
    setToasts(prev => [...prev, { id, message, type }])
  }, [])

  const removeToast = React.useCallback((id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      {toasts.map(t => (
        <Toast key={t.id} message={t.message} type={t.type} onClose={() => removeToast(t.id)} />
      ))}
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = React.useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}
