import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useToast } from '@/components/ui/toast'
import { Card, CardContent } from '@/components/ui/card'
import { Edit3, Trash2, Save, ArrowUp, ArrowDown, Plus, X, FileText } from 'lucide-react'

const SECTION_TYPES = [
  'summary', 'experience', 'education', 'skills', 'projects',
  'certifications', 'languages', 'publications', 'awards', 'links', 'custom',
]

interface PreviewSection {
  section_type: string
  title: string
  content: { text: string }
  sort_order: number
}

interface ResumePreviewProps {
  sections: PreviewSection[]
  title: string
  onSave: (title: string, sections: PreviewSection[]) => void
  onCancel: () => void
  saving?: boolean
}

export function ResumePreview({ sections: initialSections, title: initialTitle, onSave, onCancel, saving }: ResumePreviewProps) {
  const [title, setTitle] = useState(initialTitle)
  const [sections, setSections] = useState<PreviewSection[]>(initialSections)
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [editContent, setEditContent] = useState('')
  const [editType, setEditType] = useState('')
  const [showAdd, setShowAdd] = useState(false)
  const [newType, setNewType] = useState('custom')
  const [newTitle, setNewTitle] = useState('')
  const [newContent, setNewContent] = useState('')
  const { addToast } = useToast()

  const handleMove = (index: number, direction: 'up' | 'down') => {
    const target = direction === 'up' ? index - 1 : index + 1
    if (target < 0 || target >= sections.length) return
    const copy = [...sections]
    ;[copy[index], copy[target]] = [copy[target], copy[index]]
    setSections(copy.map((s, i) => ({ ...s, sort_order: i })))
  }

  const handleRemove = (index: number) => {
    setSections(prev => prev.filter((_, i) => i !== index).map((s, i) => ({ ...s, sort_order: i })))
  }

  const handleStartEdit = (index: number) => {
    setEditingIndex(index)
    setEditTitle(sections[index].title)
    setEditContent(sections[index].content?.text || '')
    setEditType(sections[index].section_type)
  }

  const handleSaveEdit = () => {
    if (editingIndex === null) return
    setSections(prev => prev.map((s, i) =>
      i === editingIndex
        ? { ...s, title: editTitle, content: { text: editContent }, section_type: editType }
        : s
    ))
    setEditingIndex(null)
    addToast('Section updated', 'success')
  }

  const handleAdd = () => {
    if (!newContent.trim() && !newTitle.trim()) return
    setSections(prev => [
      ...prev,
      {
        section_type: newType,
        title: newTitle || newType.charAt(0).toUpperCase() + newType.slice(1),
        content: { text: newContent.trim() },
        sort_order: prev.length,
      },
    ])
    setShowAdd(false)
    setNewType('custom')
    setNewTitle('')
    setNewContent('')
    addToast('Section added', 'success')
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Preview Resume</h2>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={onCancel}>
            <X className="h-4 w-4 mr-1" /> Cancel
          </Button>
          <Button size="sm" onClick={() => onSave(title, sections)} disabled={saving}>
            <Save className="h-4 w-4 mr-1" /> {saving ? 'Saving...' : 'Save Resume'}
          </Button>
        </div>
      </div>

      <div>
        <label className="text-xs text-muted-foreground block mb-1">Resume Title</label>
        <Input value={title} onChange={e => setTitle(e.target.value)} className="font-semibold" />
      </div>

      <Card>
        <CardContent className="p-4 space-y-3">
          {sections.map((section, index) => (
            <div key={index} className="rounded-lg border border-glass-border p-3">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-primary shrink-0" />
                  <span className="text-xs text-muted-foreground uppercase">{section.section_type}</span>
                </div>
                <div className="flex gap-1">
                  <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => handleMove(index, 'up')} disabled={index === 0} aria-label="Move up">
                    <ArrowUp className="h-3 w-3" />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => handleMove(index, 'down')} disabled={index === sections.length - 1} aria-label="Move down">
                    <ArrowDown className="h-3 w-3" />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => handleStartEdit(index)} aria-label="Edit section">
                    <Edit3 className="h-3 w-3" />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => handleRemove(index)} aria-label="Remove section">
                    <Trash2 className="h-3 w-3 text-error" />
                  </Button>
                </div>
              </div>

              {editingIndex === index ? (
                <div className="space-y-2" onClick={e => e.stopPropagation()}>
                  <select
                    className="w-full rounded-md border border-glass-border bg-dark-800 px-2 py-1.5 text-xs text-foreground"
                    value={editType}
                    onChange={e => setEditType(e.target.value)}
                  >
                    {SECTION_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                  <input
                    className="w-full rounded-md border border-glass-border bg-dark-800 px-2 py-1.5 text-sm font-medium text-foreground"
                    value={editTitle}
                    onChange={e => setEditTitle(e.target.value)}
                    placeholder="Section title"
                  />
                  <textarea
                    className="w-full rounded-md border border-glass-border bg-dark-800 px-2 py-1.5 text-sm text-foreground min-h-[80px]"
                    value={editContent}
                    onChange={e => setEditContent(e.target.value)}
                    placeholder="Section content"
                  />
                  <div className="flex gap-2">
                    <Button size="sm" onClick={handleSaveEdit}>Done</Button>
                    <Button variant="ghost" size="sm" onClick={() => setEditingIndex(null)}>Cancel</Button>
                  </div>
                </div>
              ) : (
                <div>
                  <p className="text-sm font-medium">{section.title}</p>
                  {section.content?.text && (
                    <p className="text-xs text-muted-foreground mt-1 whitespace-pre-wrap line-clamp-3">{section.content.text}</p>
                  )}
                </div>
              )}
            </div>
          ))}

          {showAdd ? (
            <div className="rounded-lg border border-dashed border-glass-border p-3 space-y-2">
              <select
                className="w-full rounded-md border border-glass-border bg-dark-800 px-2 py-1.5 text-xs text-foreground"
                value={newType}
                onChange={e => setNewType(e.target.value)}
              >
                {SECTION_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
              <input
                className="w-full rounded-md border border-glass-border bg-dark-800 px-2 py-1.5 text-sm text-foreground"
                value={newTitle}
                onChange={e => setNewTitle(e.target.value)}
                placeholder="Section title"
              />
              <textarea
                className="w-full rounded-md border border-glass-border bg-dark-800 px-2 py-1.5 text-sm text-foreground min-h-[60px]"
                value={newContent}
                onChange={e => setNewContent(e.target.value)}
                placeholder="Section content"
              />
              <div className="flex gap-2">
                <Button size="sm" onClick={handleAdd}>Add</Button>
                <Button variant="ghost" size="sm" onClick={() => setShowAdd(false)}>Cancel</Button>
              </div>
            </div>
          ) : (
            <Button variant="outline" size="sm" className="w-full" onClick={() => setShowAdd(true)}>
              <Plus className="h-4 w-4 mr-1" /> Add Section
            </Button>
          )}
        </CardContent>
      </Card>

      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={onCancel}>
          <X className="h-4 w-4 mr-1" /> Cancel
        </Button>
        <Button onClick={() => onSave(title, sections)} disabled={saving}>
          <Save className="h-4 w-4 mr-1" /> {saving ? 'Saving...' : 'Save Resume'}
        </Button>
      </div>
    </div>
  )
}
