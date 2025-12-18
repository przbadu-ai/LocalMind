import {
  MessageSquare,
  Plus,
  Settings,
  Minus,
  Square,
  X,
  Pin,
  Archive
} from "lucide-react"
import { NavLink, useLocation, useNavigate } from "react-router-dom"
import { getCurrentWebviewWindow } from '@tauri-apps/api/webviewWindow';
import { useState, useEffect } from "react"
import { chatService, type Chat } from "@/services/chat-service"

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { Button } from "@/components/ui/button"

const navigationItems = [
  { title: "Chats", url: "/chats", icon: MessageSquare },
]

export function AppSidebar() {
  const location = useLocation()
  const navigate = useNavigate()
  const currentPath = location.pathname
  const [recentChats, setRecentChats] = useState<Chat[]>([])
  const [isLoadingChats, setIsLoadingChats] = useState(true)

  const isActive = (path: string) => currentPath === path

  // Load recent chats from the database
  useEffect(() => {
    const loadRecentChats = async () => {
      try {
        setIsLoadingChats(true)
        const chats = await chatService.getRecentChats(30, false)
        setRecentChats(chats)
      } catch (error) {
        console.error('Failed to load recent chats:', error)
      } finally {
        setIsLoadingChats(false)
      }
    }

    loadRecentChats()

    // Listen for chat updates
    window.addEventListener('chats-updated', loadRecentChats)

    // Reload chats when navigating to a new chat
    const intervalId = setInterval(loadRecentChats, 30000) // Refresh every 30 seconds
    return () => {
      clearInterval(intervalId)
      window.removeEventListener('chats-updated', loadRecentChats)
    }
  }, [])

  const handleNewChat = () => {
    // Navigate to home page which has the chat interface for new chats
    navigate('/')
  }

  const handleMinimize = async () => {
    try {
      const appWindow = getCurrentWebviewWindow();
      await appWindow.minimize();
    } catch (err) {
      console.error('Failed to minimize:', err);
    }
  };

  const handleMaximize = async () => {
    try {
      const appWindow = getCurrentWebviewWindow();
      await appWindow.toggleMaximize();
    } catch (err) {
      console.error('Failed to maximize:', err);
    }
  };

  const handleClose = async () => {
    try {
      const appWindow = getCurrentWebviewWindow();
      await appWindow.close();
    } catch (err) {
      console.error('Failed to close:', err);
    }
  };

  return (
    <Sidebar className="border-r border-sidebar-border">
      <SidebarHeader className="p-0">
        {/* Window controls and drag region */}
        {/* <div
          data-tauri-drag-region
          className="flex items-center justify-between h-[55px] px-3"
        >
          <div
            className="flex items-center gap-1"
            style={{ position: 'fixed', top: 20, left: 10, width: '250px', zIndex: 10 }}
          >
            <button
              onClick={handleClose}
              className="p-1.5 rounded hover:bg-red-500 hover:text-white transition-colors"
              aria-label="Close"
            >
              <X className="h-3 w-3" />
            </button>
            <button
              onClick={handleMinimize}
              className="p-1.5 rounded hover:bg-sidebar-accent transition-colors"
              aria-label="Minimize"
            >
              <Minus className="h-3 w-3" />
            </button>
            <button
              onClick={handleMaximize}
              className="p-1.5 rounded hover:bg-sidebar-accent transition-colors"
              aria-label="Maximize"
            >
              <Square className="h-3 w-3" />
            </button>
            <div className="bg-sidebar-accent ml-2">
              <SidebarTrigger className="h-8 w-8" />
            </div>
          </div>
        </div> */}

        {/* New chat button */}
        <div className="p-4">
          <Button
            variant="outline"
            className="w-full justify-start gap-2 h-10 bg-primary/10 border-primary/20 hover:bg-primary/20"
            onClick={handleNewChat}
          >
            <Plus className="h-4 w-4" />
            New chat
          </Button>
        </div>
      </SidebarHeader>

      <SidebarContent className="px-4">
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {navigationItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    asChild
                    className={`${isActive(item.url)
                      ? "bg-sidebar-accent text-sidebar-accent-foreground"
                      : "hover:bg-sidebar-accent/50"
                      }`}
                  >
                    <NavLink to={item.url} className="flex items-center gap-3">
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel className="text-sidebar-foreground/60 text-xs font-medium mb-2">
            Recent Chats
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {isLoadingChats ? (
                <div className="px-3 py-2 text-sm text-sidebar-foreground/60">
                  Loading chats...
                </div>
              ) : recentChats.length === 0 ? (
                <div className="px-3 py-2 text-sm text-sidebar-foreground/60">
                  No chats yet. Start a new conversation!
                </div>
              ) : (
                recentChats.map((chat) => (
                  <SidebarMenuItem key={chat.id}>
                    <SidebarMenuButton
                      asChild
                      className="h-8 text-sm hover:bg-sidebar-accent/50 text-sidebar-foreground/80 hover:text-sidebar-foreground"
                    >
                      <NavLink to={`/chats/${chat.id}`} className="flex items-center gap-2">
                        {chat.is_pinned && <Pin className="h-3 w-3 flex-shrink-0" />}
                        {chat.is_archived && <Archive className="h-3 w-3 flex-shrink-0" />}
                        <MessageSquare className="h-4 w-4 flex-shrink-0" />
                        <span className="truncate">{chat.title}</span>
                      </NavLink>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))
              )}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-4 border-t border-sidebar-border">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              className={`${isActive("/settings")
                ? "bg-sidebar-accent text-sidebar-accent-foreground"
                : "hover:bg-sidebar-accent/50"
                }`}
            >
              <NavLink to="/settings" className="flex items-center gap-3">
                <Settings className="h-4 w-4" />
                <span>Settings</span>
              </NavLink>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  )
}