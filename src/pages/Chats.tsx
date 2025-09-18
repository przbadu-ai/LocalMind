import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { MessageSquare, FileText, Code, Globe, Youtube, Database, Brain, Cpu, Mail, Filter, Upload, Building, Server, Bug, Bell, Smartphone, Palette } from "lucide-react"

const recentChats = [
  { id: "open-source-rag", icon: MessageSquare, title: "Open-source RAG document tool", lastMessage: "Building a desktop RAG application with Tauri", timestamp: "2 hours ago" },
  { id: "untitled-1", icon: FileText, title: "Untitled", lastMessage: "New conversation", timestamp: "1 day ago" },
  { id: "code-critique", icon: Code, title: "Code critique and improvement workflow", lastMessage: "Reviewing code structure and patterns", timestamp: "2 days ago" },
  { id: "ollama-override", icon: Globe, title: "Agio Ollama Base URL Override", lastMessage: "Configuring Ollama base URL settings", timestamp: "3 days ago" }, 
  { id: "youtube-transcript", icon: Youtube, title: "YouTube Transcript API Script Project", lastMessage: "Building YouTube transcript extraction", timestamp: "4 days ago" },
  { id: "streamlit-pdf", icon: Database, title: "Streamlit PDF Chat with EmbedChain", lastMessage: "PDF processing with vector embeddings", timestamp: "5 days ago" },
]


export default function Chats() {
  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold mb-2">Chats</h1>
        <p className="text-muted-foreground">Your conversation history</p>
      </div>

      <div className="grid gap-4">
        {recentChats.map((chat) => (
          <Card key={chat.id} className="hover:bg-accent/50 transition-colors">
            <CardContent className="p-0">
              <Button variant="ghost" className="w-full h-auto p-4 justify-start" asChild>
                <Link to={`/chats/${chat.id}`}>
                  <div className="flex items-start gap-4 w-full">
                    <chat.icon className="h-5 w-5 text-primary mt-1" />
                    <div className="flex-1 text-left">
                      <h3 className="font-medium text-foreground mb-1">{chat.title}</h3>
                      <p className="text-sm text-muted-foreground mb-2 line-clamp-2">{chat.lastMessage}</p>
                      <p className="text-xs text-muted-foreground">{chat.timestamp}</p>
                    </div>
                  </div>
                </Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}