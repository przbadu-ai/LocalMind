import { useState } from "react"
import { 
  MessageSquare, 
  Plus, 
  Folder, 
  Box, 
  User,
  Settings,
  ChevronDown,
  Sparkles
} from "lucide-react"
import { NavLink, useLocation } from "react-router-dom"

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
import { Avatar, AvatarFallback } from "@/components/ui/avatar"

const navigationItems = [
  { title: "Chats", url: "/chats", icon: MessageSquare },
  { title: "Projects", url: "/projects", icon: Folder },
  { title: "Artifacts", url: "/artifacts", icon: Box },
]

const recentItems = [
  "Open-source RAG document tool",
  "Code critique and improvement suggestions",
  "Agno Ollama Base URL Override",
  "YouTube Transcript API Script Update",
  "Streamlit PDF Chat with Embeddings",
  "Docker Compose Vector Database Setup",
  "HuggingFace Text Embedding Model Integration",
  "vLLM Model Selection for RTX 5090",
  "Rails User Email Update Script",
  "SQL Filtering Non-Numeric Approach",
  "Rails 6.1 Parameter Permit Upgrade",
  "Open-Source AI Chat App Architecture",
]

export function AppSidebar() {
  const location = useLocation()
  const currentPath = location.pathname

  const isActive = (path: string) => currentPath === path

  return (
    <Sidebar className="border-r border-sidebar-border">
      <SidebarHeader className="p-4">
        <Button
          variant="outline"
          className="w-full justify-start gap-2 h-10 bg-primary/10 border-primary/20 hover:bg-primary/20"
        >
          <Plus className="h-4 w-4" />
          New chat
        </Button>
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
                  <SidebarMenuButton className="h-8 text-sm hover:bg-sidebar-accent/50 text-sidebar-foreground/80 hover:text-sidebar-foreground">
                    <span className="truncate">{item}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-4">
        <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-sidebar-accent/50 cursor-pointer">
          <Avatar className="h-8 w-8">
            <AvatarFallback className="bg-primary text-primary-foreground text-sm">
              PZ
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 text-left">
            <p className="text-sm font-medium text-sidebar-foreground">przbadu</p>
            <p className="text-xs text-sidebar-foreground/60">Procurementexpress</p>
          </div>
          <ChevronDown className="h-4 w-4 text-sidebar-foreground/60" />
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}