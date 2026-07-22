import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// Dev proxy: the SPA talks to the backend with same-origin relative URLs
// (/api, /ws) — no CORS or host juggling in app code. The proxy target is
// configuration (frontend/.env, VITE_API_TARGET), not a hardcoded host.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, __dirname, "");
  const apiTarget = env.VITE_API_TARGET ?? "http://localhost:8000";
  return {
    plugins: [react()],
    resolve: { alias: { "@": path.resolve(__dirname, "src") } },
    server: {
      port: 5173,
      proxy: {
        "/api": { target: apiTarget, changeOrigin: true },
        "/ws": { target: apiTarget.replace(/^http/, "ws"), ws: true },
      },
    },
  };
});