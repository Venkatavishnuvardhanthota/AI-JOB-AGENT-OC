import { useState, useRef, useEffect } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Check, X, Pencil } from 'lucide-react'

interface InlineEditProps {
  value: string
  onSave: (value: string) => void
  placeholder?: string
  className?: string
  type?: 'text' | 'date'
}

export function InlineEdit({ value, onSave, placeholder, className = '', type = 'text' }: InlineEditProps) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(value)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (editing) inputRef.current?.focus()
  }, [editing])

  useEffect(() => {
    setDraft(value)
  }, [value])

  const handleSave = () => {
    if (draft !== value) onSave(draft)
    setEditing(false)
  }

  const handleCancel = () => {
    setDraft(value)
    setEditing(false)
  }

  if (editing) {
    return (
      <div className="flex items-center gap-1">
        <Input
          ref={inputRef}
          type={type}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') handleSave(); if (e.key === 'Escape') handleCancel() }}
          className="h-7 text-xs w-32"
          placeholder={placeholder}
        />
        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={handleSave} aria-label="Save">
          <Check className="h-3 w-3" />
        </Button>
        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={handleCancel} aria-label="Cancel">
          <X className="h-3 w-3" />
        </Button>
      </div>
    )
  }

  return (
    <button
      onClick={() => setEditing(true)}
      className={`group flex items-center gap-1 text-sm hover:text-primary transition-colors ${className}`}
      aria-label={`Edit ${placeholder || 'value'}`}
    >
      <span>{value || placeholder || '—'}</span>
      <Pencil className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground" />
    </button>
  )
}
