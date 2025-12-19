/**
 * Model Selector Component
 *
 * A dropdown component that allows users to select an LLM model,
 * grouped by provider (Ollama, OpenAI, etc.)
 */

import { useState, useEffect, useCallback } from "react"
import { ChevronDown, Loader2, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { settingsService, type ProviderWithModels } from "@/services/settings-service"

interface ModelSelectorProps {
  selectedProvider?: string | null
  selectedModel?: string | null
  onChange: (provider: string, model: string) => void
  disabled?: boolean
  compact?: boolean
}

export function ModelSelector({
  selectedProvider,
  selectedModel,
  onChange,
  disabled = false,
  compact = false,
}: ModelSelectorProps) {
  const [providers, setProviders] = useState<ProviderWithModels[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [defaultProvider, setDefaultProvider] = useState<string | null>(null)
  const [defaultModel, setDefaultModel] = useState<string | null>(null)

  const loadProviders = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await settingsService.getAllProvidersWithModels()
      setProviders(data.providers)
      setDefaultProvider(data.default_provider)
      setDefaultModel(data.default_model)
    } catch (err) {
      setError("Failed to load models")
      console.error("Failed to load providers:", err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadProviders()
  }, [loadProviders])

  // Generate value string for the select (provider:model format)
  const currentValue = selectedProvider && selectedModel
    ? `${selectedProvider}:${selectedModel}`
    : defaultProvider && defaultModel
      ? `${defaultProvider}:${defaultModel}`
      : undefined

  // Parse selection and call onChange
  const handleValueChange = (value: string) => {
    const [provider, ...modelParts] = value.split(":")
    const model = modelParts.join(":") // Handle models with colons in name
    onChange(provider, model)
  }

  // Get display text for current selection
  const getDisplayText = () => {
    if (selectedProvider && selectedModel) {
      const provider = providers.find(p => p.name === selectedProvider)
      const label = provider?.label || selectedProvider
      return compact ? selectedModel : `${label}: ${selectedModel}`
    }
    if (defaultProvider && defaultModel) {
      const provider = providers.find(p => p.name === defaultProvider)
      const label = provider?.label || defaultProvider
      return compact ? defaultModel : `${label}: ${defaultModel}`
    }
    return "Select model"
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-muted-foreground text-sm">
        <Loader2 className="h-3 w-3 animate-spin" />
        <span>Loading models...</span>
      </div>
    )
  }

  if (error || providers.length === 0) {
    return (
      <div className="flex items-center gap-2 text-muted-foreground text-sm">
        <span>{error || "No providers configured"}</span>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={loadProviders}
        >
          <RefreshCw className="h-3 w-3" />
        </Button>
      </div>
    )
  }

  return (
    <Select
      value={currentValue}
      onValueChange={handleValueChange}
      disabled={disabled}
    >
      <SelectTrigger className={compact ? "h-7 w-auto min-w-[150px] text-xs" : "h-8 w-auto min-w-[200px] text-sm"}>
        <SelectValue placeholder="Select model">
          {getDisplayText()}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {providers.map((provider) => (
          <SelectGroup key={provider.name}>
            <SelectLabel className="text-xs font-semibold text-muted-foreground">
              {provider.label}
              {provider.is_default && (
                <span className="ml-2 text-xs font-normal text-primary">(default)</span>
              )}
            </SelectLabel>
            {provider.models.length > 0 ? (
              provider.models.map((model) => (
                <SelectItem
                  key={`${provider.name}:${model}`}
                  value={`${provider.name}:${model}`}
                  className="pl-4"
                >
                  {model}
                  {provider.configured_model === model && (
                    <span className="ml-2 text-xs text-muted-foreground">(configured)</span>
                  )}
                </SelectItem>
              ))
            ) : (
              <SelectItem
                value={`${provider.name}:${provider.configured_model || "unavailable"}`}
                className="pl-4 text-muted-foreground"
                disabled={!provider.configured_model}
              >
                {provider.configured_model || "No models available"}
              </SelectItem>
            )}
          </SelectGroup>
        ))}
      </SelectContent>
    </Select>
  )
}

export default ModelSelector
