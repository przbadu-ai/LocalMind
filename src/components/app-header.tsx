import { ThemeToggle } from "@/components/theme-toggle"
import { useHeaderStore } from "@/stores/useHeaderStore"

export function AppHeader() {
  const title = useHeaderStore((state) => state.title)

  return (
    <header className="flex h-14 items-center justify-between bg-background px-4 border-b gap-4">
      <div className="flex items-center gap-2 min-w-0 flex-1">
        <span className="text-lg font-semibold truncate">{title || ""}</span>
      </div>

      <div className="flex items-center gap-2">
        {/* <Button variant="ghost" size="icon" className="h-8 w-8">
          <Bell className="h-4 w-4" />
        </Button> */}
        <ThemeToggle />
      </div>
    </header>
  )
}