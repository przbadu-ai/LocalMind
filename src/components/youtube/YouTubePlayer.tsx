import { useEffect, useRef, useState } from "react"

interface YouTubePlayerProps {
  videoId: string
  startTime?: number
  onTimeUpdate?: (time: number) => void
  className?: string
}

export function YouTubePlayer({
  videoId,
  startTime = 0,
  onTimeUpdate,
  className = "",
}: YouTubePlayerProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const [isReady, setIsReady] = useState(false)

  // Generate embed URL with parameters
  const embedUrl = `https://www.youtube.com/embed/${videoId}?enablejsapi=1&rel=0&modestbranding=1${startTime > 0 ? `&start=${Math.floor(startTime)}` : ""}`

  useEffect(() => {
    // Listen for messages from the iframe
    const handleMessage = (event: MessageEvent) => {
      if (event.origin !== "https://www.youtube.com") return

      try {
        const data = JSON.parse(event.data)
        if (data.event === "onReady") {
          setIsReady(true)
        }
        if (data.event === "infoDelivery" && data.info?.currentTime !== undefined) {
          onTimeUpdate?.(data.info.currentTime)
        }
      } catch {
        // Ignore non-JSON messages
      }
    }

    window.addEventListener("message", handleMessage)
    return () => window.removeEventListener("message", handleMessage)
  }, [onTimeUpdate])

  // Seek to timestamp function
  const seekTo = (seconds: number) => {
    if (iframeRef.current?.contentWindow) {
      iframeRef.current.contentWindow.postMessage(
        JSON.stringify({
          event: "command",
          func: "seekTo",
          args: [seconds, true],
        }),
        "*"
      )
      // Also play after seeking
      iframeRef.current.contentWindow.postMessage(
        JSON.stringify({
          event: "command",
          func: "playVideo",
          args: [],
        }),
        "*"
      )
    }
  }

  // Expose seekTo function via ref or custom event
  useEffect(() => {
    const handleSeekEvent = (event: CustomEvent<{ seconds: number }>) => {
      seekTo(event.detail.seconds)
    }

    window.addEventListener("youtube-seek", handleSeekEvent as EventListener)
    return () => window.removeEventListener("youtube-seek", handleSeekEvent as EventListener)
  }, [])

  return (
    <div className={`relative w-full aspect-video rounded-lg overflow-hidden bg-black ${className}`}>
      <iframe
        ref={iframeRef}
        src={embedUrl}
        className="absolute inset-0 w-full h-full"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
        title="YouTube video player"
      />
    </div>
  )
}

// Helper function to trigger seek from outside the component
export function seekYouTubeVideo(seconds: number) {
  window.dispatchEvent(
    new CustomEvent("youtube-seek", { detail: { seconds } })
  )
}
