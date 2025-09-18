import { Routes, Route } from "react-router-dom";
import { MainContent } from "./components/app-content";
import Chats from "./pages/Chats";
import Settings from "./pages/Settings";
import NotFound from "./pages/NotFound";
import ChatDetail from "./pages/ChatDetails";

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<MainContent />} />
      <Route path="/chats" element={<Chats />} />
      <Route path="/settings" element={<Settings />} />
      <Route path="/chats/:chatId" element={<ChatDetail />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}