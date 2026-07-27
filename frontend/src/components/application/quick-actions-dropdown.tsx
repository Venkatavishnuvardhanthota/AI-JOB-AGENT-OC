import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import { applicationService } from '@/services/application'
import { useToast } from '@/components/ui/toast'
import { getAllowedTransitions, getStatusLabel, PRIORITY_LABELS, PRIORITY_ORDER } from '@/services/status'
import { MoreHorizontal, ExternalLink, Archive, Trash2, StickyNote, Clock, ArrowRight } from 'lucide-react'
import type { Application, ApplicationStatus, ApplicationPriority } from '@/types'

interface QuickActionsDropdownProps {
  application: Application
  onAddNote?: (id: string) => void
}

export function QuickActionsDropdown({ application, onAddNote }: QuickActionsDropdownProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { addToast } = useToast()

  const updateMutation = useMutation({
    mutationFn: (data: { status?: ApplicationStatus; priority?: ApplicationPriority }) =>
      applicationService.update(application.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] })
      addToast('Application updated', 'success')
    },
    onError: () => addToast('Failed to update', 'error'),
  })

  const archiveMutation = useMutation({
    mutationFn: (id: string) => applicationService.update(id, { status: 'archived' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] })
      addToast('Application archived', 'info')
    },
    onError: () => addToast('Failed to archive', 'error'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => applicationService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] })
      addToast('Application deleted', 'info')
    },
    onError: () => addToast('Failed to delete', 'error'),
  })

  const allowedStatuses = getAllowedTransitions(application.status)

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="h-8 w-8" aria-label="Quick actions">
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        <DropdownMenuItem onSelect={() => navigate(`/applications/${application.id}`)}>
          <ExternalLink className="h-4 w-4 mr-2" /> Open
        </DropdownMenuItem>

        {onAddNote && (
          <DropdownMenuItem onSelect={() => onAddNote(application.id)}>
            <StickyNote className="h-4 w-4 mr-2" /> Add Note
          </DropdownMenuItem>
        )}

        <DropdownMenuItem onSelect={() => navigate(`/applications/${application.id}?tab=timeline`)}>
          <Clock className="h-4 w-4 mr-2" /> View Timeline
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        {allowedStatuses.length > 0 && (
          <div className="px-2 py-1.5">
            <p className="text-xs text-muted-foreground mb-1">Change Status</p>
            <div className="space-y-0.5 max-h-32 overflow-y-auto">
              {allowedStatuses.map(s => (
                <button
                  key={s}
                  className="flex w-full items-center gap-2 rounded px-2 py-1 text-xs hover:bg-white/5 transition-colors"
                  onClick={() => updateMutation.mutate({ status: s })}
                >
                  <ArrowRight className="h-3 w-3" />
                  {getStatusLabel(s)}
                </button>
              ))}
            </div>
          </div>
        )}

        <DropdownMenuSeparator />

        <div className="px-2 py-1.5">
          <p className="text-xs text-muted-foreground mb-1">Change Priority</p>
          <div className="space-y-0.5">
            {PRIORITY_ORDER.map(p => (
              <button
                key={p}
                className="flex w-full items-center gap-2 rounded px-2 py-1 text-xs hover:bg-white/5 transition-colors"
                onClick={() => updateMutation.mutate({ priority: p as ApplicationPriority })}
              >
                {PRIORITY_LABELS[p]}
              </button>
            ))}
          </div>
        </div>

        <DropdownMenuSeparator />

        <DropdownMenuItem onSelect={() => { if (confirm('Archive this application?')) archiveMutation.mutate(application.id) }}>
          <Archive className="h-4 w-4 mr-2" /> Archive
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={() => { if (confirm('Delete this application?')) deleteMutation.mutate(application.id) }} className="text-error">
          <Trash2 className="h-4 w-4 mr-2" /> Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
