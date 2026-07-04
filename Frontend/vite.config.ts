/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      // Proxy all /api/* calls to the FastAPI backend during development.
      // The backend also accepts requests directly at the path root (no /api prefix),
      // so we strip the /api prefix when forwarding.
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  build: {
    // Split large dependencies into separate chunks to improve caching and
    // reduce initial load time.
    rollupOptions: {
      output: {
        manualChunks: {
          // React core
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          // Charting
          'vendor-charts': ['recharts'],
          // State + utilities
          'vendor-state': ['zustand'],
          // Icons
          'vendor-icons': ['lucide-react'],
        },
      },
    },
    // Raise the warning threshold slightly so normal chunks don't spam warnings
    chunkSizeWarningLimit: 600,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './vitest.setup.ts',
  },
})
