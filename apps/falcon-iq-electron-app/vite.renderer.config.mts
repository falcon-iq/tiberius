import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import tsconfigPaths from "vite-tsconfig-paths";
import { tanstackRouter } from '@tanstack/router-plugin/vite';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// https://vitejs.dev/config
export default defineConfig({
  plugins: [
    tailwindcss(),
    tanstackRouter({
      routesDirectory: './src/renderer/routes',
      generatedRouteTree: './src/renderer/types/routeTree.gen.ts',
    }),
    react(),
    tsconfigPaths(),
  ],
  resolve: {
    alias: {
      '@libs/shared': resolve(__dirname, '../../libs/shared/src'),
    },
  },
});
