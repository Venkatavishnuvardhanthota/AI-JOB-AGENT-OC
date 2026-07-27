import { useMemo, useState, useRef, useEffect } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { ArrowLeftRight, Plus, Minus, Pencil } from 'lucide-react'

interface CompareProps {
  original: string
  edited: string
  labelA?: string
  labelB?: string
}

function normalizeHtml(html: string) {
  const tmp = document.createElement('div')
  tmp.innerHTML = html
  return (tmp.textContent || tmp.innerText || '').trim()
}

function computeDiff(a: string, b: string) {
  const linesA = normalizeHtml(a).split('\n').filter(Boolean)
  const linesB = normalizeHtml(b).split('\n').filter(Boolean)
  const changes: { type: 'added' | 'removed' | 'modified'; text: string }[] = []
  const maxLen = Math.max(linesA.length, linesB.length)
  for (let i = 0; i < maxLen; i++) {
    const lineA = linesA[i] || ''
    const lineB = linesB[i] || ''
    if (lineA && !lineB) changes.push({ type: 'removed', text: lineA })
    else if (!lineA && lineB) changes.push({ type: 'added', text: lineB })
    else if (lineA !== lineB) changes.push({ type: 'modified', text: `${lineA} → ${lineB}` })
  }
  return changes
}

export function CoverLetterCompare({ original, edited, labelA = 'Original', labelB = 'Edited' }: CompareProps) {
  const [syncScroll, setSyncScroll] = useState(true)
  const leftRef = useRef<HTMLDivElement>(null)
  const rightRef = useRef<HTMLDivElement>(null)
  const changes = useMemo(() => computeDiff(original, edited), [original, edited])
  const added = changes.filter(c => c.type === 'added').length
  const removed = changes.filter(c => c.type === 'removed').length
  const modified = changes.filter(c => c.type === 'modified').length

  useEffect(() => {
    if (!syncScroll) return
    const left = leftRef.current
    const right = rightRef.current
    if (!left || !right) return
    const handleScroll = () => { right.scrollTop = left.scrollTop }
    const handleScrollR = () => { left.scrollTop = right.scrollTop }
    left.addEventListener('scroll', handleScroll)
    right.addEventListener('scroll', handleScrollR)
    return () => { left.removeEventListener('scroll', handleScroll); right.removeEventListener('scroll', handleScrollR) }
  }, [syncScroll])

  const renderContent = (html: string) => (
    <div className="prose prose-invert max-w-none text-sm" dangerouslySetInnerHTML={{ __html: html || '<p class="text-muted-foreground">No content</p>' }} />
  )

  return (
    <div className="space-y-4" role="region" aria-label="Version comparison">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <ArrowLeftRight className="h-4 w-4" /> Compare Versions
        </h3>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 text-xs">
            <Badge variant="success" className="text-[10px]"><Plus className="h-3 w-3 mr-0.5" />{added}</Badge>
            <Badge variant="destructive" className="text-[10px]"><Minus className="h-3 w-3 mr-0.5" />{removed}</Badge>
            <Badge variant="warning" className="text-[10px]"><Pencil className="h-3 w-3 mr-0.5" />{modified}</Badge>
          </div>
          <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={() => setSyncScroll(!syncScroll)}>
            {syncScroll ? 'Sync: On' : 'Sync: Off'}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardContent className="p-0">
            <div className="px-3 py-2 text-xs font-semibold text-muted-foreground border-b border-glass-border">
              {labelA}
            </div>
            <div ref={leftRef} className="p-3 max-h-60 overflow-y-auto">
              {renderContent(original)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-0">
            <div className="px-3 py-2 text-xs font-semibold text-muted-foreground border-b border-glass-border">
              {labelB}
            </div>
            <div ref={rightRef} className="p-3 max-h-60 overflow-y-auto">
              {renderContent(edited)}
            </div>
          </CardContent>
        </Card>
      </div>

      {changes.length > 0 && (
        <div className="space-y-1 max-h-48 overflow-y-auto">
          <p className="text-xs text-muted-foreground">Changes detected ({changes.length})</p>
          {changes.map((c, i) => (
            <div key={i} className={cn(
              'rounded-lg px-3 py-1.5 text-xs border',
              c.type === 'added' && 'bg-success/5 border-success/20 text-success',
              c.type === 'removed' && 'bg-error/5 border-error/20 text-error',
              c.type === 'modified' && 'bg-warning/5 border-warning/20 text-warning',
            )}>
              <Badge variant={c.type === 'added' ? 'success' : c.type === 'removed' ? 'destructive' : 'warning'} className="text-[10px] mr-2">
                {c.type}
              </Badge>
              {c.text}
            </div>
          ))}
        </div>
      )}

      {changes.length === 0 && (
        <p className="text-sm text-muted-foreground text-center py-4">No differences found between versions.</p>
      )}
    </div>
  )
}
