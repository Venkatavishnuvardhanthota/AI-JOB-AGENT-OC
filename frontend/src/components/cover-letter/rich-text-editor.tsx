import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  Bold, Italic, Underline, Heading1, Heading2, Heading3,
  List, ListOrdered, Quote, Link, Undo2, Redo2, Eye, EyeOff,
} from 'lucide-react'

interface RichTextEditorProps {
  value: string
  onChange: (html: string) => void
  placeholder?: string
  minHeight?: string
  readOnly?: boolean
}

function stripHtml(html: string) {
  const tmp = document.createElement('div')
  tmp.innerHTML = html
  return tmp.textContent || tmp.innerText || ''
}

function wordCount(text: string) { return text.trim() ? text.trim().split(/\s+/).length : 0 }
function charCount(text: string) { return text.length }
function readingTime(text: string) { return Math.max(1, Math.round(wordCount(text) / 200)) }

export function RichTextEditor({
  value, onChange, placeholder = 'Start writing your cover letter...',
  minHeight = '400px', readOnly = false,
}: RichTextEditorProps) {
  const editorRef = useRef<HTMLDivElement>(null)
  const [showPreview, setShowPreview] = useState(false)
  const [showLinkInput, setShowLinkInput] = useState(false)
  const [linkUrl, setLinkUrl] = useState('')

  const plainText = useMemo(() => stripHtml(value), [value])
  const wc = useMemo(() => wordCount(plainText), [plainText])
  const cc = useMemo(() => charCount(plainText), [plainText])
  const rt = useMemo(() => readingTime(plainText), [plainText])

  useEffect(() => {
    if (editorRef.current && editorRef.current.innerHTML !== value) {
      editorRef.current.innerHTML = value
    }
  }, [value])

  const exec = useCallback((command: string, val?: string) => {
    document.execCommand(command, false, val)
    editorRef.current?.focus()
    if (onChange) onChange(editorRef.current?.innerHTML || '')
  }, [onChange])

  const handleInput = useCallback(() => {
    if (onChange) onChange(editorRef.current?.innerHTML || '')
  }, [onChange])

  const handleLink = useCallback(() => {
    if (showLinkInput && linkUrl) {
      exec('createLink', linkUrl)
      setShowLinkInput(false); setLinkUrl('')
    } else {
      const sel = window.getSelection()
      if (sel && !sel.isCollapsed) { setShowLinkInput(true); setLinkUrl('') }
    }
  }, [exec, showLinkInput, linkUrl])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); /* parent handles autosave */ }
    if ((e.ctrlKey || e.metaKey) && e.key === 'b') { e.preventDefault(); exec('bold') }
    if ((e.ctrlKey || e.metaKey) && e.key === 'i') { e.preventDefault(); exec('italic') }
    if ((e.ctrlKey || e.metaKey) && e.key === 'u') { e.preventDefault(); exec('underline') }
    if ((e.ctrlKey || e.metaKey) && e.key === 'z') { e.preventDefault(); exec('undo') }
    if ((e.ctrlKey || e.metaKey) && e.key === 'y') { e.preventDefault(); exec('redo') }
  }, [exec])

  const ToolBtn = ({ icon: Icon, cmd, val, title }: { icon: any; cmd: string; val?: string; title: string }) => (
    <Button variant="ghost" size="sm" onClick={() => exec(cmd, val)} title={title} aria-label={title} className="h-8 w-8 p-0">
      <Icon className="h-4 w-4" />
    </Button>
  )

  const editContent = (
    <div
      ref={editorRef}
      contentEditable={!readOnly}
      onInput={handleInput}
      onKeyDown={handleKeyDown}
      className="w-full rounded-lg border border-glass-border bg-dark-800 p-4 text-sm leading-relaxed overflow-y-auto focus:outline-none focus:border-accent/50 prose prose-invert max-w-none"
      style={{ minHeight, maxHeight: '70vh' }}
      role="textbox"
      aria-multiline="true"
      aria-label="Cover letter editor"
      data-placeholder={placeholder}
      dangerouslySetInnerHTML={{ __html: value || '' }}
    />
  )

  const previewContent = (
    <div
      className="w-full rounded-lg border border-glass-border bg-white p-8 text-sm leading-relaxed overflow-y-auto prose max-w-none"
      style={{ minHeight, maxHeight: '70vh' }}
      dangerouslySetInnerHTML={{ __html: value || '<p class="text-gray-400">No content to preview</p>' }}
    />
  )

  return (
    <div className="space-y-2" role="region" aria-label="Rich text editor">
      <div className="flex flex-wrap items-center gap-0.5 p-1.5 rounded-lg border border-glass-border bg-dark-800/50">
        <ToolBtn icon={Bold} cmd="bold" title="Bold (Ctrl+B)" />
        <ToolBtn icon={Italic} cmd="italic" title="Italic (Ctrl+I)" />
        <ToolBtn icon={Underline} cmd="underline" title="Underline (Ctrl+U)" />
        <div className="w-px h-6 mx-1 bg-glass-border" />
        <ToolBtn icon={Heading1} cmd="formatBlock" val="h1" title="Heading 1" />
        <ToolBtn icon={Heading2} cmd="formatBlock" val="h2" title="Heading 2" />
        <ToolBtn icon={Heading3} cmd="formatBlock" val="h3" title="Heading 3" />
        <div className="w-px h-6 mx-1 bg-glass-border" />
        <ToolBtn icon={List} cmd="insertUnorderedList" title="Bullet list" />
        <ToolBtn icon={ListOrdered} cmd="insertOrderedList" title="Numbered list" />
        <ToolBtn icon={Quote} cmd="formatBlock" val="blockquote" title="Block quote" />
        <div className="w-px h-6 mx-1 bg-glass-border" />
        <Button variant="ghost" size="sm" onClick={handleLink} title="Insert link" aria-label="Insert link" className="h-8 w-8 p-0">
          <Link className="h-4 w-4" />
        </Button>
        {showLinkInput && (
          <span className="flex items-center gap-1 ml-1">
            <input
              value={linkUrl}
              onChange={e => setLinkUrl(e.target.value)}
              placeholder="https://..."
              className="w-40 h-7 px-2 text-xs rounded border border-glass-border bg-dark-800"
              autoFocus
              onKeyDown={e => { if (e.key === 'Enter') handleLink(); if (e.key === 'Escape') setShowLinkInput(false) }}
            />
          </span>
        )}
        <div className="w-px h-6 mx-1 bg-glass-border" />
        <ToolBtn icon={Undo2} cmd="undo" title="Undo (Ctrl+Z)" />
        <ToolBtn icon={Redo2} cmd="redo" title="Redo (Ctrl+Y)" />

        <div className="ml-auto flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => setShowPreview(!showPreview)}
            title={showPreview ? 'Edit mode' : 'Print preview'} aria-label={showPreview ? 'Edit mode' : 'Print preview'}
            className="h-8 text-xs gap-1">
            {showPreview ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
            {showPreview ? 'Edit' : 'Preview'}
          </Button>
        </div>
      </div>

      {showPreview ? previewContent : editContent}

      <div className="flex items-center gap-4 text-xs text-muted-foreground px-1">
        <span>{wc} words</span>
        <span>{cc} characters</span>
        <span>{rt} min read</span>
      </div>
    </div>
  )
}

export function renderToText(html: string): string {
  return stripHtml(html)
}
