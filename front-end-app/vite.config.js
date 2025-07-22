import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: 'localhost',
    port: 5173,
    hmr: {
      host: 'j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net'
    },
    proxy: {
      '/api': {
        target: 'https://j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net/',
        changeOrigin: true,
        secure: false,      
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
});
