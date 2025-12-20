import { useState } from "react"
import { Check, Copy } from "lucide-react"
import { Button } from "@/components/ui/button"

interface JsonViewerProps {
  data: unknown
  label?: string
}

export function JsonViewer({ data, label }: JsonViewerProps) {
  const [copied, setCopied] = useState(false)
  const jsonString = JSON.stringify(data, null, 2)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(jsonString)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="relative">
      {label && (
        <div className="text-sm text-muted-foreground mb-1">{label}</div>
      )}
      <div className="bg-muted rounded-md p-3 font-mono text-sm overflow-x-auto relative">
        <Button
          size="icon"
          variant="ghost"
          className="absolute top-2 right-2 h-6 w-6 text-muted-foreground hover:text-foreground"
          onClick={handleCopy}
        >
          {copied ? (
            <Check className="h-3 w-3" />
          ) : (
            <Copy className="h-3 w-3" />
          )}
        </Button>
        <pre className="text-emerald-600 dark:text-emerald-400 pr-8">{jsonString}</pre>
      </div>
    </div>
  )
}
