import { ThemeToggle } from "@/components/theme-toggle"

export function AppHeader() {
  return (
    <header className="flex h-14 items-center justify-between bg-background px-4">
      <div className="flex items-center gap-2">
        {/* <span className="text-sm font-semibold">LocalMind</span> */}
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