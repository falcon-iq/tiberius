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
      '@libs/shared/utils': resolve(__dirname, '../../libs/shared/utils/src/index.ts'),
      '@libs/shared/validations': resolve(__dirname, '../../libs/shared/validations/src/index.ts'),
      '@libs/integrations/github/auth': resolve(__dirname, '../../libs/integrations/github/src/auth.ts'),
    },
  },
});
