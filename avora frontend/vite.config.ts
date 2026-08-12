import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // Forward analytics API calls to the real analytics server (default :8787)
      '/api': {
        target: process.env.VITE_ANALYTICS_PROXY || 'http://localhost:8787',
        changeOrigin: true,
      },
    },
  },
})
