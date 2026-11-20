import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 80,
    proxy: {
      // Проксирует запросы от Vite dev server на FastAPI backend
      '/api': {
        target: 'http://app:8000',
        changeOrigin: true,
      },
    },
  },
});
