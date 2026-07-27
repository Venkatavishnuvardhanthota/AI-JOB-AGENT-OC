import { useCallback, useState, useRef, useEffect } from 'react'
import { useAIAssistCoverLetter } from '@/api/hooks'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { Loader2, Sparkles, Check, X } from 'lucide-react'

const AI_ACTIONS = [
  { id: 'rewrite', label: 'Rewrite' },
  { id: 'shorten', label: 'Shorten' },
  { id: 'expand', label: 'Expand' },
  { id: 'grammar', label: 'Improve Grammar' },
  { id: 'improve', label: 'Improve' },
  { id: 'professional', label: 'Make Professional' },
  { id: 'technical', label: 'Make Technical' },
  { id: 'executive', label: 'Make Executive' },
  { id: 'friendly', label: 'Make Friendly' },
  { id: 'remove_repetition', label: 'Remove Repetition' },
] as const

interface AIInlineEditProps {
  coverLetterId: string
  content: string
  onApplyEdit: (newContent: string) => void
}

export function AIInlineEdit({ coverLetterId, content, onApplyEdit }: AIInlineEditProps) {
  const aiAssist = useAIAssistCoverLetter()
  const [selectedText, setSelectedText] = useState('')
  const [showActions, setShowActions] = useState(false)
  const [suggestion, setSuggestion] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const panelRef = useRef<HTMLDivElement>(null)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [replacing, setReplacing] = useState('')

  const handleTextSelect = useCallback(() => {
    const sel = window.getSelection()
    if (!sel || sel.isCollapsed || !sel.toString().trim()) {
      setShowActions(false); return
    }
    const text = sel.toString().trim()
    if (text.length < 3) { setShowActions(false); return }
    setSelectedText(text)
    const range = sel.getRangeAt(0)
    const rect = range.getBoundingClientRect()
    setPosition({ x: rect.left + rect.width / 2, y: rect.top - 10 })
    setShowActions(true)
    setSuggestion(null)
    setError('')
  }, [])

  useEffect(() => {
    document.addEventListener('mouseup', handleTextSelect)
    return () => document.removeEventListener('mouseup', handleTextSelect)
  }, [handleTextSelect])

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setShowActions(false); setSuggestion(null)
      }
    }
    if (showActions) {
      setTimeout(() => document.addEventListener('mousedown', handleClickOutside), 0)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showActions])

  const handleAction = useCallback(async (actionId: string) => {
    setLoading(true)
    setError('')
    setReplacing(actionId)
    try {
      const result = await aiAssist.mutateAsync({
        id: coverLetterId,
        data: { section: selectedText, instruction: actionId, context: content },
      }) as any
      const edited = result.edited || ''
      if (edited && edited !== selectedText) {
        setSuggestion(edited)
      } else {
        setError('AI returned no changes. Try a different action.')
      }
    } catch {
      setError('AI assist failed. Try again.')
    } finally {
      setLoading(false)
      setReplacing('')
    }
  }, [coverLetterId, selectedText, content, aiAssist])

  const handleAccept = useCallback(() => {
    if (!suggestion) return
    const newContent = content.replace(selectedText, suggestion)
    onApplyEdit(newContent)
    setSuggestion(null)
    setShowActions(false)
    setSelectedText('')
  }, [content, selectedText, suggestion, onApplyEdit])

  const handleReject = useCallback(() => {
    setSuggestion(null)
    setError('')
  }, [])

  if (!showActions && !suggestion) return null

  return (
    <div ref={panelRef} style={{ position: 'fixed', zIndex: 100 }}>
      {showActions && !suggestion && (
        <div
          className="bg-dark-800 border border-glass-border rounded-xl shadow-xl p-2 min-w-[200px]"
          style={{ left: Math.max(10, position.x - 100), top: Math.max(10, position.y - 220) }}
          role="dialog"
          aria-label="AI editing actions"
        >
          <div className="flex items-center gap-2 mb-1 px-2 py-1 text-xs text-muted-foreground border-b border-glass-border">
            <Sparkles className="h-3 w-3 text-accent" />
            <span>AI Edit</span>
          </div>
          <div className="space-y-0.5">
            {AI_ACTIONS.map(action => (
              <button
                key={action.id}
                onClick={() => handleAction(action.id)}
                disabled={loading}
                className={cn(
                  'w-full text-left px-2 py-1.5 rounded-md text-xs transition-colors',
                  'hover:bg-white/5 text-muted-foreground hover:text-foreground',
                  loading && replacing === action.id && 'animate-pulse text-accent',
                )}
                aria-label={action.label}
              >
                {loading && replacing === action.id ? (
                  <span className="flex items-center gap-2"><Loader2 className="h-3 w-3 animate-spin" />{action.label}...</span>
                ) : action.label}
              </button>
            ))}
          </div>
          {error && <p className="px-2 pt-1 text-xs text-error">{error}</p>}
        </div>
      )}

      {suggestion && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
          onClick={handleReject}
        >
          <div
            className="bg-dark-800 border border-glass-border rounded-xl shadow-2xl p-5 w-[560px] max-w-[90vw] max-h-[80vh] overflow-y-auto"
            onClick={e => e.stopPropagation()}
            role="dialog"
            aria-label="AI suggestion preview"
          >
            <div className="flex items-center gap-2 mb-3 pb-2 border-b border-glass-border">
              <Sparkles className="h-4 w-4 text-accent" />
              <h3 className="text-sm font-semibold">AI Suggestion</h3>
            </div>

            <div className="space-y-3">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Original</p>
                <div className="rounded-lg border border-glass-border bg-dark-900 p-3 text-sm whitespace-pre-wrap line-through opacity-60">
                  {selectedText}
                </div>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Suggested</p>
                <div className="rounded-lg border border-accent/30 bg-accent/5 p-3 text-sm whitespace-pre-wrap">
                  {suggestion}
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-4">
              <Button variant="outline" size="sm" onClick={handleReject}>
                <X className="h-4 w-4 mr-1" /> Reject
              </Button>
              <Button size="sm" onClick={handleAccept}>
                <Check className="h-4 w-4 mr-1" /> Accept
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
