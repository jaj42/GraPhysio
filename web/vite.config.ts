import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The backend (FastAPI) runs separately on :8000 and already allows CORS from
// localhost, so the frontend talks to it directly via VITE_API_BASE. We also
// expose a /api proxy as a same-origin alternative (set VITE_API_BASE=/api).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ''),
      },
    },
  },
});
