import { StrictMode } from "react";
import ReactDOM from "react-dom/client";

import "./index.css";
import App from "./App";
import { ClerkProviderWrapper } from "@/components/clerk-provider-wrapper";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <StrictMode>
    <ClerkProviderWrapper>
      <App />
    </ClerkProviderWrapper>
  </StrictMode>
);
