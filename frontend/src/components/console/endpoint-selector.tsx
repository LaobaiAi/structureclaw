'use client'

import { useStore } from '@/lib/stores/context'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { cn } from '@/lib/utils'

/**
 * EndpointSelector - Dual select for endpoint and mode selection
 *
 * CONS-01: User can select endpoint (agent-run, chat-message, chat-execute)
 * CONS-02: User can select mode (chat, execute, auto)
 * Mode selector is disabled when chat-execute endpoint is selected
 */
export function EndpointSelector() {
  const endpoint = useStore((state) => state.endpoint)
  const mode = useStore((state) => state.mode)
  const setEndpoint = useStore((state) => state.setEndpoint)
  const setMode = useStore((state) => state.setMode)

  // Mode is disabled when endpoint is chat-execute
  const isModeDisabled = endpoint === 'chat-execute'

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {/* Endpoint Select */}
      <div className="space-y-2">
        <label htmlFor="endpoint-select" className="text-sm font-medium">
          Endpoint
        </label>
        <Select
          value={endpoint}
          onValueChange={(value) => setEndpoint(value as typeof endpoint)}
        >
          <SelectTrigger id="endpoint-select" aria-label="Endpoint">
            <SelectValue placeholder="Select endpoint" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="chat-message">chat-message</SelectItem>
            <SelectItem value="chat-execute">chat-execute</SelectItem>
            <SelectItem value="agent-run">agent-run</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Mode Select */}
      <div className="space-y-2">
        <label htmlFor="mode-select" className="text-sm font-medium">
          Mode
        </label>
        <Select
          value={mode}
          onValueChange={(value) => setMode(value as typeof mode)}
          disabled={isModeDisabled}
        >
          <SelectTrigger
            id="mode-select"
            aria-label="Mode"
            className={cn(isModeDisabled && 'cursor-not-allowed opacity-50')}
          >
            <SelectValue placeholder="Select mode" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="chat">chat</SelectItem>
            <SelectItem value="execute">execute</SelectItem>
            <SelectItem value="auto">auto</SelectItem>
          </SelectContent>
        </Select>
        {isModeDisabled && (
          <p className="text-xs text-muted-foreground">
            Mode is fixed for chat-execute endpoint
          </p>
        )}
      </div>
    </div>
  )
}
