import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { noteService } from '@/services/note'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/layout/empty-state'
import { useToast } from '@/components/ui/toast'
import { StickyNote, Plus, Pencil, Trash2, Search, X, Check } from 'lucide-react'
import type { ApplicationNote } from '@/types'

interface ApplicationNotesProps {
  applicationId: string
}

export function ApplicationNotes({ applicationId }: ApplicationNotesProps) {
  const [search, setSearch] = useState('')
  const [editingNote, setEditingNote] = useState<ApplicationNote | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const queryClient = useQueryClient()
  const { addToast } = useToast()

  const { data: notes, isLoading } = useQuery({
    queryKey: ['applications', applicationId, 'notes'],
    queryFn: () => noteService.list(applicationId),
    enabled: !!applicationId,
  })

  const createMutation = useMutation({
    mutationFn: (data: { title: string; content: string }) => noteService.create(applicationId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications', applicationId, 'notes'] })
      setIsCreating(false)
      setTitle('')
      setContent('')
      addToast('Note created', 'success')
    },
    onError: () => addToast('Failed to create note', 'error'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { title?: string; content?: string } }) =>
      noteService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications', applicationId, 'notes'] })
      setEditingNote(null)
      setTitle('')
      setContent('')
      addToast('Note updated', 'success')
    },
    onError: () => addToast('Failed to update note', 'error'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => noteService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications', applicationId, 'notes'] })
      addToast('Note deleted', 'info')
    },
    onError: () => addToast('Failed to delete note', 'error'),
  })

  const filtered = notes?.filter(n =>
    !search || n.title.toLowerCase().includes(search.toLowerCase()) || n.content.toLowerCase().includes(search.toLowerCase())
  )

  const handleCreate = () => {
    if (!title.trim() || !content.trim()) return
    createMutation.mutate({ title: title.trim(), content: content.trim() })
  }

  const handleUpdate = () => {
    if (!editingNote) return
    updateMutation.mutate({
      id: editingNote.id,
      data: { title: title.trim() || undefined, content: content.trim() || undefined },
    })
  }

  const startEdit = (note: ApplicationNote) => {
    setEditingNote(note)
    setTitle(note.title)
    setContent(note.content)
    setIsCreating(false)
  }

  const cancelEdit = () => {
    setEditingNote(null)
    setIsCreating(false)
    setTitle('')
    setContent('')
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Notes</CardTitle>
          {!isCreating && !editingNote && (
            <Button variant="outline" size="sm" onClick={() => { setIsCreating(true); setEditingNote(null); setTitle(''); setContent('') }}>
              <Plus className="h-4 w-4 mr-1" /> Add Note
            </Button>
          )}
        </div>
        {notes && notes.length > 0 && (
          <div className="relative mt-2">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search notes..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8"
              aria-label="Search notes"
            />
          </div>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? (
          Array.from({ length: 2 }).map((_, i) => <Skeleton key={i} className="h-20 w-full" />)
        ) : !notes?.length && !isCreating ? (
          <EmptyState icon={StickyNote} title="No notes" description="Add notes to track your thoughts about this application." />
        ) : (
          <>
            {(isCreating || editingNote) && (
              <div className="space-y-2 p-3 rounded-lg bg-dark-800/50 border border-glass-border">
                <Input
                  placeholder="Note title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  aria-label="Note title"
                />
                <textarea
                  placeholder="Note content..."
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  className="w-full min-h-[80px] rounded-md border border-glass-border bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                  aria-label="Note content"
                />
                <div className="flex gap-2 justify-end">
                  <Button variant="outline" size="sm" onClick={cancelEdit}>
                    <X className="h-4 w-4 mr-1" /> Cancel
                  </Button>
                  <Button
                    size="sm"
                    onClick={editingNote ? handleUpdate : handleCreate}
                    disabled={!title.trim() || !content.trim() || createMutation.isPending || updateMutation.isPending}
                  >
                    <Check className="h-4 w-4 mr-1" /> {editingNote ? 'Update' : 'Create'}
                  </Button>
                </div>
              </div>
            )}
            {filtered?.map(note => (
              <div key={note.id} className="p-3 rounded-lg bg-dark-800/30 border border-glass-border">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-medium">{note.title}</h4>
                    <p className="text-sm text-muted-foreground mt-1 whitespace-pre-wrap">{note.content}</p>
                    <p className="text-xs text-muted-foreground mt-2">
                      {new Date(note.created_at).toLocaleString()}
                      {note.updated_at !== note.created_at && ' (edited)'}
                    </p>
                  </div>
                  <div className="flex gap-1 shrink-0">
                    <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => startEdit(note)} aria-label={`Edit ${note.title}`}>
                      <Pencil className="h-3.5 w-3.5" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-7 w-7 text-error" onClick={() => deleteMutation.mutate(note.id)} aria-label={`Delete ${note.title}`}>
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </>
        )}
      </CardContent>
    </Card>
  )
}
