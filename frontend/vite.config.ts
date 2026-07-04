import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The backend serves the built SPA from ./static, so the app is same-origin in
// production. In dev, proxy the API and WebSocket to the backend on :8080.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8080",
      "/ws": { target: "ws://localhost:8080", ws: true },
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
