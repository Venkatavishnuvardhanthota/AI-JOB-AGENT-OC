import { Badge } from '@/components/ui/badge'
import type { CapabilityInfo } from '@/types'

const capabilityLabels: Record<keyof CapabilityInfo, string> = {
  chat: 'Chat',
  streaming: 'Streaming',
  vision: 'Vision',
  json_mode: 'JSON Mode',
  embeddings: 'Embeddings',
  reasoning: 'Reasoning',
  function_calling: 'Function Calling',
  tool_calling: 'Tool Calling',
  system_prompt_support: 'System Prompts',
  structured_output: 'Structured Output',
}

interface ProviderCapabilitiesProps {
  capabilities?: CapabilityInfo
}

export function ProviderCapabilities({ capabilities }: ProviderCapabilitiesProps) {
  if (!capabilities) return <span className="text-xs text-muted-foreground">No capability info</span>

  const enabled = Object.entries(capabilities)
    .filter(([, v]) => v === true)
    .map(([k]) => k as keyof CapabilityInfo)

  if (enabled.length === 0) return <span className="text-xs text-muted-foreground">Basic only</span>

  return (
    <div className="flex flex-wrap gap-1">
      {enabled.map(key => (
        <Badge key={key} variant="outline" className="text-[10px] px-1.5 py-0">
          {capabilityLabels[key] || key}
        </Badge>
      ))}
    </div>
  )
}
