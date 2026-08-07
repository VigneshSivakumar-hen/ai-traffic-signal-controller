import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// During `npm run dev`, proxy API calls to the FastAPI backend so you can
// edit the UI with hot-reload while still hitting a real running pipeline.
// The production build (npm run build) doesn't need this: FastAPI serves
// the built files directly, same origin, no proxy involved.
const BACKEND = 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/health': BACKEND,
      '/status': BACKEND,
      '/metrics': BACKEND,
      '/signal': BACKEND,
      '/frame': BACKEND,
      '/pipeline': BACKEND,
    },
  },
  build: {
    outDir: 'dist',
  },
})
