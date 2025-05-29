import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: 'localhost',
    port: 5173,
    hmr: {
      host: 'localhost'
    },
    proxy: {
      '/api': {
        target: 'http://localhost/',
        changeOrigin: true,
        secure: false,      
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
});
