import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    cssMinify: false,
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // Bundle Three.js + R3F ecosystem into one cacheable vendor chunk
          if (
            id.includes('three') ||
            id.includes('@react-three') ||
            id.includes('react-three')
          ) {
            return 'vendor-three';
          }
          // React core into its own tiny chunk
          if (id.includes('node_modules/react') || id.includes('node_modules/react-dom')) {
            return 'vendor-react';
          }
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      // Forward /api/* and /static/* to the FastAPI backend
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
