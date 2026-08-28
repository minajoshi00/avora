import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // Forward all /api calls to the AVORA backend (default :3000). Can be overridden with VITE_ANALYTICS_PROXY.
      '/api': {
        target: process.env.VITE_ANALYTICS_PROXY || 'http://localhost:3000',
        changeOrigin: true,
      },
    },
  },
})
