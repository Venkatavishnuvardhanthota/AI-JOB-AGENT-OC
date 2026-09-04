import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useAIPrompts } from '@/api/hooks'
import {
  FileText,
  Variable,
  MessageSquare,
} from 'lucide-react'

export function PromptTemplatesPanel() {
  const { data: prompts, isLoading, isError } = useAIPrompts()

  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><FileText className="h-5 w-5 text-primary" />Prompt Templates</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          {[1, 2, 3].map(i => <Skeleton key={i} className="h-16 w-full" />)}
        </CardContent>
      </Card>
    )
  }

  if (isError) {
    return (
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><FileText className="h-5 w-5 text-primary" />Prompt Templates</CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm text-error">Failed to load prompt templates</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-primary" />
          Prompt Templates ({prompts?.length || 0})
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {prompts?.map(t => (
          <div
            key={t.name}
            className="rounded-lg border border-glass-border p-3 space-y-1.5"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium">{t.name}</p>
                {t.description && (
                  <p className="text-xs text-muted-foreground">{t.description}</p>
                )}
              </div>
              <div className="flex items-center gap-1 shrink-0">
                {t.version && <span className="text-[10px] text-muted-foreground">v{t.version}</span>}
                {t.has_system_prompt && (
                  <Badge variant="outline" className="text-[10px] px-1 py-0">
                    <MessageSquare className="h-2.5 w-2.5 mr-0.5" />
                    System
                  </Badge>
                )}
              </div>
            </div>
            {t.variables && t.variables.length > 0 && (
              <div className="flex items-center gap-1 flex-wrap">
                <Variable className="h-3 w-3 text-muted-foreground" />
                {t.variables.map(v => (
                  <Badge key={v} variant="secondary" className="text-[10px] px-1 py-0">{v}</Badge>
                ))}
              </div>
            )}
          </div>
        ))}
        {(!prompts || prompts.length === 0) && (
          <p className="text-sm text-muted-foreground text-center py-4">No prompt templates registered</p>
        )}
      </CardContent>
    </Card>
  )
}
