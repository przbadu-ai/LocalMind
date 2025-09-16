import { createHashRouter } from "react-router";
import App from "./pages/App";

const router = createHashRouter([
  {
    path: "/",
    element: <App />,
  },
  {
    path: "/chat",
    element: <div>Chat Page</div>,
  }
]);

export { router };