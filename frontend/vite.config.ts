import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { proxy: { '/api': 'http://127.0.0.1:8001', '/admin': 'http://127.0.0.1:8001', '/static': 'http://127.0.0.1:8001' } },
  build: { chunkSizeWarningLimit: 1800 },
  worker: { format: 'es' },
})
