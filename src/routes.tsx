import { createHashRouter } from "react-router";
import App from "./App";

const router = createHashRouter([
  {
    path: "/*",
    element: <App />,
  }
]);

export { router };