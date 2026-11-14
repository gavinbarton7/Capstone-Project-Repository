import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Forward API calls to the Python backend (python backend/app.py).
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
