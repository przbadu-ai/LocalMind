import { useState, useRef, useEffect } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Search, Clock } from "lucide-react"
import { seekYouTubeVideo } from "./YouTubePlayer"

export interface TranscriptSegment {
  text: string
  start: number
  duration: number
}

interface TranscriptViewerProps {
  segments: TranscriptSegment[]
  currentTime?: number
  onTimestampClick?: (seconds: number) => void
  className?: string
}

function formatTimestamp(seconds: number): string {
  const totalSeconds = Math.floor(seconds)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const secs = totalSeconds % 60

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }
  return `${minutes}:${secs.toString().padStart(2, "0")}`
}

export function TranscriptViewer({
  segments,
  currentTime = 0,
  onTimestampClick,
  className = "",
}: TranscriptViewerProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const currentSegmentRef = useRef<HTMLDivElement>(null)

  // Filter segments based on search query
  const filteredSegments = searchQuery
    ? segments.filter((seg) =>
        seg.text.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : segments

  // Find current segment based on playback time
  const currentSegmentIndex = segments.findIndex(
    (seg) => currentTime >= seg.start && currentTime < seg.start + seg.duration
  )

  // Handle timestamp click
  const handleTimestampClick = (seconds: number) => {
    seekYouTubeVideo(seconds)
    onTimestampClick?.(seconds)
  }

  // Auto-scroll to current segment when not searching
  useEffect(() => {
    if (!searchQuery && currentSegmentRef.current) {
      currentSegmentRef.current.scrollIntoView({
        behavior: "smooth",
        block: "center",
      })
    }
  }, [currentSegmentIndex, searchQuery])

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Search box */}
      <div className="flex-shrink-0 p-3 border-b border-border">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search transcript..."
            className="pl-9"
          />
        </div>
        {searchQuery && (
          <p className="text-xs text-muted-foreground mt-2">
            Found {filteredSegments.length} matching segments
          </p>
        )}
      </div>

      {/* Transcript segments */}
      <ScrollArea className="flex-1" ref={scrollAreaRef}>
        <div className="p-3 space-y-1">
          {filteredSegments.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              {searchQuery ? "No matching segments found" : "No transcript available"}
            </p>
          ) : (
            filteredSegments.map((segment, index) => {
              const isCurrentSegment =
                !searchQuery && segments.indexOf(segment) === currentSegmentIndex

              return (
                <div
                  key={`${segment.start}-${index}`}
                  ref={isCurrentSegment ? currentSegmentRef : null}
                  className={`flex gap-3 p-2 rounded-lg transition-colors ${
                    isCurrentSegment
                      ? "bg-primary/10 border-l-2 border-primary"
                      : "hover:bg-muted/50"
                  }`}
                >
                  <Button
                    variant={isCurrentSegment ? "default" : "outline"}
                    size="sm"
                    className="flex-shrink-0 h-7 px-2 font-mono text-xs"
                    onClick={() => handleTimestampClick(segment.start)}
                  >
                    <Clock className="h-3 w-3 mr-1" />
                    {formatTimestamp(segment.start)}
                  </Button>
                  <p
                    className={`text-sm leading-relaxed ${
                      isCurrentSegment ? "font-medium" : ""
                    }`}
                  >
                    {segment.text}
                  </p>
                </div>
              )
            })
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
