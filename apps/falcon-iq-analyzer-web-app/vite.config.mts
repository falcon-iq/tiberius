import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import tsconfigPaths from 'vite-tsconfig-paths';
import { tanstackRouter } from '@tanstack/router-plugin/vite';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    tanstackRouter({
      routesDirectory: './src/routes',
      generatedRouteTree: './src/types/routeTree.gen.ts',
    }),
    tsconfigPaths(),
  ],
  resolve: {
    alias: {
      '@libs/shared': resolve(__dirname, '../../libs/shared/src'),
    },
  },
  server: {
    proxy: {
      '/sites': 'http://localhost:8000',
      '/crawl': 'http://localhost:8000',
      '/analyze': 'http://localhost:8000',
      '/analyses': 'http://localhost:8000',
      '/benchmark': 'http://localhost:8000',
      '/benchmarks': 'http://localhost:8000',
      '/report': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
});
