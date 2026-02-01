import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from "path"

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: true, // Crucial: Listen on 0.0.0.0 for Docker
    strictPort: true,
    port: 5173,
    watch: {
      usePolling: true, // Fixes HMR file watching in some Docker environments
    },
  }
})
