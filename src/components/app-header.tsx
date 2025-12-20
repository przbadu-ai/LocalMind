import { SignedIn, UserButton } from "@clerk/clerk-react"
import { ThemeToggle } from "@/components/theme-toggle"
import { useHeaderStore } from "@/stores/useHeaderStore"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { AUTH_ENABLED } from "@/config/app-config"

export function AppHeader() {
  const title = useHeaderStore((state) => state.title)

  return (
    <header className="flex h-14 items-center justify-between bg-background px-4 border-b gap-4">
      <div className="flex items-center gap-2 min-w-0 flex-1">
        <SidebarTrigger className="shrink-0" />
        <span className="text-lg font-semibold truncate">{title || ""}</span>
      </div>

      <div className="flex items-center gap-2">
        <ThemeToggle />
        {AUTH_ENABLED && (
          <SignedIn>
            <UserButton
              appearance={{
                elements: {
                  avatarBox: "h-8 w-8",
                },
              }}
            />
          </SignedIn>
        )}
      </div>
    </header>
  )
}