import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { formatDistanceToNow } from "date-fns"
import {
  MessageSquare,
  MoreVertical,
  Trash2,
  Edit,
  Loader2
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
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
import { chatService, type Chat } from "@/services/chat-service"

export default function Chats() {
  const [chats, setChats] = useState<Chat[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [renameId, setRenameId] = useState<string | null>(null)
  const [newTitle, setNewTitle] = useState("")

  useEffect(() => {
    loadChats()
  }, [])

  const loadChats = async () => {
    try {
      setIsLoading(true)
      const data = await chatService.getRecentChats(100)
      setChats(data)
    } catch (error) {
      console.error("Failed to load chats:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!deleteId) return
    try {
      await chatService.deleteChat(deleteId)
      setChats(chats.filter(c => c.id !== deleteId))
      window.dispatchEvent(new Event('chats-updated'))
      setDeleteId(null)
    } catch (error) {
      console.error("Failed to delete chat:", error)
    }
  }

  const handleRename = async () => {
    if (!renameId || !newTitle.trim()) return
    try {
      const updated = await chatService.updateChat(renameId, { title: newTitle })
      setChats(chats.map(c => c.id === renameId ? updated : c))
      window.dispatchEvent(new Event('chats-updated'))
      setRenameId(null)
      setNewTitle("")
    } catch (error) {
      console.error("Failed to rename chat:", error)
    }
  }

  const openRenameDialog = (chat: Chat) => {
    setRenameId(chat.id)
    setNewTitle(chat.title)
  }

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold mb-2">Chats</h1>
        <p className="text-muted-foreground">Your conversation history</p>
      </div>

      {chats.length === 0 ? (
        <div className="text-center text-muted-foreground py-12">
          No chats found. Start a new conversation!
        </div>
      ) : (
        <div className="grid gap-4">
          {chats.map((chat) => (
            <Card key={chat.id} className="hover:bg-accent/50 transition-colors group">
              <CardContent className="p-0 flex items-center">
                <Button variant="ghost" className="flex-1 h-auto p-4 justify-start" asChild>
                  <Link to={`/chats/${chat.id}`}>
                    <div className="flex items-start gap-4 w-full">
                      <MessageSquare className="h-5 w-5 text-primary mt-1" />
                      <div className="flex-1 text-left">
                        <h3 className="font-medium text-foreground mb-1 mobile-check-title">{chat.title}</h3>
                        <p className="text-xs text-muted-foreground">
                          {formatDistanceToNow(new Date(chat.updated_at), { addSuffix: true })}
                        </p>
                      </div>
                    </div>
                  </Link>
                </Button>

                <div className="pr-4">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity">
                        <MoreVertical className="h-4 w-4" />
                        <span className="sr-only">Actions</span>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => openRenameDialog(chat)}>
                        <Edit className="mr-2 h-4 w-4" />
                        Rename
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => setDeleteId(chat.id)} className="text-destructive focus:text-destructive">
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

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
    </div>
  )
}