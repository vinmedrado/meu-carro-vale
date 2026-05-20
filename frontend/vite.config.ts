import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: { host: "0.0.0.0", port: 5180 },
  preview: { host: "0.0.0.0", port: 5180 },
  build: {
    chunkSizeWarningLimit: 700,
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          if (id.includes('node_modules/react') || id.includes('node_modules/react-dom')) return 'vendor';
          return undefined;
        },
      },
    },
  },
});
