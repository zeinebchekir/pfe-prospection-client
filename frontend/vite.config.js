import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: true,
    port: 5173,
    proxy: {
      // Proxy all /api requests to Django backend
      // This avoids CORS issues in development
      '/api': {
        target: process.env.VITE_PROXY_TARGET || 'http://web:8000',
        changeOrigin: true,
        secure: false,
      },
      '/notifications': {           // ← ajouter
        target: process.env.VITE_FASTAPI_URL || 'http://etl-fastapi:8000',
        changeOrigin: false,
        secure: false,
        ws: true,                   // ← support SSE/WebSocket
      },
      '/segmentation': {              // ← ajouter
        target: 'http://etl-fastapi:8000',
        changeOrigin: true,
        secure: false,
      },
      '/entreprises': {        // ← ajouter
    target: 'http://etl-fastapi:8000',
    changeOrigin: true,
    secure: false,
      },
      '/ia': {                 // ← ajouter
        target: 'http://ia-ml:8002',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
