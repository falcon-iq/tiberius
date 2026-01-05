import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import tsconfigPaths from "vite-tsconfig-paths";
import { tanstackRouter } from '@tanstack/router-plugin/vite';

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
});
