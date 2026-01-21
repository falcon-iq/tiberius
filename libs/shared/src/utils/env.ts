/**
 * Environment detection utilities for Node.js, Electron, and browser contexts.
 */

/**
 * Type guard for checking if import.meta has Vite env properties
 */
interface ViteImportMeta {
  env: {
    DEV?: boolean;
    MODE?: string;
  };
}

/**
 * Checks if the application is running in development mode.
 *
 * Works in:
 * - Node.js: checks NODE_ENV
 * - Electron main process: checks NODE_ENV and VITE_DEV_SERVER_URL
 * - Electron renderer/browser: checks import.meta.env (when available)
 *
 * @returns true if in development mode, false otherwise
 */
export const isDevelopment = (): boolean => {
  // Check Node.js environment variable
  if (typeof process !== 'undefined' && process.env) {
    if (process.env['NODE_ENV'] === 'development') {
      return true;
    }
    // Electron Forge/Vite dev server indicator
    if (process.env['VITE_DEV_SERVER_URL']) {
      return true;
    }
  }

  // Check Vite's import.meta.env (browser/renderer context)
  if (typeof import.meta !== 'undefined') {
    const meta = import.meta as unknown as ViteImportMeta;
    if (meta.env) {
      return meta.env.DEV === true || meta.env.MODE === 'development';
    }
  }

  return false;
};

/**
 * Checks if the application is running in production mode.
 * @returns true if in production mode, false otherwise
 */
export const isProduction = (): boolean => {
  return !isDevelopment();
};
