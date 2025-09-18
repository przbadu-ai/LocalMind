import {
  MessageSquare,
  Plus,
  Folder,
  FileText,
  Code,
  Globe,
  Youtube,
  Database,
  Brain,
  Cpu,
  Mail,
  Filter,
  Upload,
  Building,
  Server,
  Bug,
  Bell,
  Smartphone,
  Palette,
  Minus,
  Square,
  X
} from "lucide-react"
import { NavLink, useLocation } from "react-router-dom"
import { getCurrentWebviewWindow } from '@tauri-apps/api/webviewWindow';

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
  { title: "Settings", url: "/settings", icon: Folder },
]

const recentItems = [
  { id: "open-source-rag", icon: MessageSquare, title: "Open-source RAG document tool", url: "/chats/open-source-rag" },
  { id: "untitled-1", icon: FileText, title: "Untitled", url: "/chats/untitled-1" },
  { id: "code-critique", icon: Code, title: "Code critique and improvement workflow", url: "/chats/code-critique" },
  { id: "ollama-override", icon: Globe, title: "Agio Ollama Base URL Override", url: "/chats/ollama-override" }, 
  { id: "youtube-transcript", icon: Youtube, title: "YouTube Transcript API Script Project", url: "/chats/youtube-transcript" },
  { id: "streamlit-pdf", icon: Database, title: "Streamlit PDF Chat with EmbedChain...", url: "/chats/streamlit-pdf" },
  { id: "docker-compose", icon: Database, title: "Docker Compose Vector Database...", url: "/chats/docker-compose" },
  { id: "huggingface-embedding", icon: Brain, title: "HuggingFace Text Embedding Model...", url: "/chats/huggingface-embedding" },
  { id: "vllm-model", icon: Cpu, title: "vLLM Model Selection for RTX 5060...", url: "/chats/vllm-model" },
  { id: "rails-email", icon: Mail, title: "Rails User Email Update Script", url: "/chats/rails-email" },
  { id: "sql-filtering", icon: Filter, title: "SQL Filtering Non-Numeric Approval...", url: "/chats/sql-filtering" },
  { id: "rails-api", icon: Upload, title: "Rails API Parameter Permit Upgrade", url: "/chats/rails-api" },
  { id: "ai-chat-architecture", icon: Building, title: "Open-Source AI Chat App Architecture...", url: "/chats/ai-chat-architecture" },
  { id: "untitled-2", icon: FileText, title: "Untitled", url: "/chats/untitled-2" },
  { id: "untitled-3", icon: FileText, title: "Untitled", url: "/chats/untitled-3" },
  { id: "vllm-server", icon: Server, title: "vLLM Inference Server Setup", url: "/chats/vllm-server" },
  { id: "metabase-react", icon: Database, title: "Metabase React Dashboard Integration...", url: "/chats/metabase-react" },
  { id: "untitled-4", icon: FileText, title: "Untitled", url: "/chats/untitled-4" },
  { id: "comfyui-error", icon: Bug, title: "ComfyUI Model Download Error", url: "/chats/comfyui-error" },
  { id: "untitled-5", icon: FileText, title: "Untitled", url: "/chats/untitled-5" },
  { id: "openwebui-clone", icon: Globe, title: "OpenWebUI Clone with Rails 8", url: "/chats/openwebui-clone" },
  { id: "web-push", icon: Bell, title: "Web Push Notification Troubleshooting...", url: "/chats/web-push" },
  { id: "responsive-modal", icon: Smartphone, title: "Responsive Modal CSS Media Query", url: "/chats/responsive-modal" },
  { id: "tailwind-palette", icon: Palette, title: "Tailwind Color Palette Design", url: "/chats/tailwind-palette" },
  { id: "rails-assets", icon: Upload, title: "Rails App Asset Pipeline Upgrade", url: "/chats/rails-assets" },
]

export function AppSidebar() {
  const location = useLocation()
  const currentPath = location.pathname

  const isActive = (path: string) => currentPath === path

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
        <div
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
        </div>

        {/* New chat button */}
        <div className="p-4">
          <NavLink to={"/"} className="flex items-center gap-2">
            <Button
              variant="outline"
              className="w-full justify-start gap-2 h-10 bg-primary/10 border-primary/20 hover:bg-primary/20"
            >
              <Plus className="h-4 w-4" />
              New chat
            </Button>
          </NavLink>
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
                    className={`${
                      isActive(item.url) 
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
            Recents
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {recentItems.map((item, index) => (
                <SidebarMenuItem key={index}>
                  <SidebarMenuButton asChild className="h-8 text-sm hover:bg-sidebar-accent/50 text-sidebar-foreground/80 hover:text-sidebar-foreground">
                    <NavLink to={item.url} className="flex items-center gap-2">
                      <item.icon className="h-4 w-4 flex-shrink-0" />
                      <span className="truncate">{item.title}</span>
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-4 border-t border-sidebar-border">
        <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-sidebar-accent/50 cursor-pointer">
          <div className="flex-1 text-left">
            <p className="text-sm font-medium text-sidebar-foreground">Version</p>
            <p className="text-xs text-sidebar-foreground/60">1.0.0</p>
          </div>
          {/* <ChevronDown className="h-4 w-4 text-sidebar-foreground/60" /> */}
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}