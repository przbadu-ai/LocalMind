import {
  MessageSquare,
  Plus,
  Settings,
  Pin,
  Archive,
  MoreHorizontal,
  Edit,
  Trash2,
} from "lucide-react"
import { NavLink, useLocation, useNavigate } from "react-router-dom"
import { useState, useEffect } from "react"
import { chatService, type ChatSidebarItem } from "@/services/chat-service"

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
} from "@/components/ui/sidebar"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"

const navigationItems = [
  { title: "Chats", url: "/chats", icon: MessageSquare },
]

export function AppSidebar() {
  const location = useLocation()
  const navigate = useNavigate()
  const currentPath = location.pathname
  const [recentChats, setRecentChats] = useState<ChatSidebarItem[]>([])
  const [isLoadingChats, setIsLoadingChats] = useState(true)
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [renameId, setRenameId] = useState<string | null>(null)
  const [newTitle, setNewTitle] = useState("")

  const isActive = (path: string) => currentPath === path

  // Load recent chats from the database
  useEffect(() => {
    const loadRecentChats = async () => {
      try {
        setIsLoadingChats(true)
        const chats = await chatService.getSidebarChats(30, false)
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

  const openRenameDialog = (chat: ChatSidebarItem) => {
    setRenameId(chat.id)
    setNewTitle(chat.title)
  }

  const handleRename = async () => {
    if (!renameId || !newTitle.trim()) return

    try {
      const updated = await chatService.updateChat(renameId, { title: newTitle.trim() })
      // Update local state with only the fields we need for sidebar
      setRecentChats(prev => prev.map(chat =>
        chat.id === renameId
          ? { ...chat, title: updated.title, updated_at: updated.updated_at || chat.updated_at }
          : chat
      ))
      window.dispatchEvent(new Event('chats-updated'))
    } catch (error) {
      console.error('Failed to rename chat:', error)
    } finally {
      setRenameId(null)
      setNewTitle("")
    }
  }

  const handleDelete = async () => {
    if (!deleteId) return

    try {
      await chatService.deleteChat(deleteId)
      setRecentChats(prev => prev.filter(chat => chat.id !== deleteId))
      window.dispatchEvent(new Event('chats-updated'))

      // If we're viewing the deleted chat, navigate to home
      if (currentPath === `/chats/${deleteId}`) {
        navigate('/')
      }
    } catch (error) {
      console.error('Failed to delete chat:', error)
    } finally {
      setDeleteId(null)
    }
  }

  return (
    <Sidebar className="border-r border-sidebar-border">
      <SidebarHeader className="p-0">
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
                  <SidebarMenuItem key={chat.id} className="group/item">
                    <div className="flex items-center w-full">
                      <SidebarMenuButton
                        asChild
                        className="h-8 text-sm hover:bg-sidebar-accent/50 text-sidebar-foreground/80 hover:text-sidebar-foreground flex-1 pr-1"
                      >
                        <NavLink to={`/chats/${chat.id}`} className="flex items-center gap-2">
                          {chat.is_pinned && <Pin className="h-3 w-3 flex-shrink-0" />}
                          {chat.is_archived && <Archive className="h-3 w-3 flex-shrink-0" />}
                          <MessageSquare className="h-4 w-4 flex-shrink-0" />
                          <span className="truncate">{chat.title}</span>
                        </NavLink>
                      </SidebarMenuButton>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6 opacity-0 group-hover/item:opacity-100 transition-opacity flex-shrink-0"
                          >
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-40">
                          <DropdownMenuItem onClick={() => openRenameDialog(chat)}>
                            <Edit className="h-4 w-4 mr-2" />
                            Rename
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => setDeleteId(chat.id)}
                            className="text-destructive focus:text-destructive"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
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

      {/* Delete Dialog */}
      <Dialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Chat</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this chat? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rename Dialog */}
      <Dialog open={!!renameId} onOpenChange={(open) => !open && setRenameId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename Chat</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <Input
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="Chat title"
              onKeyDown={(e) => e.key === 'Enter' && handleRename()}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRenameId(null)}>Cancel</Button>
            <Button onClick={handleRename}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Sidebar>
  )
}