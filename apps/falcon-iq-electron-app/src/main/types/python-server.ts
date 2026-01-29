/**
 * Main process-specific Python server configuration.
 * Shared types are imported from src/shared/types/python-server.ts
 */

export interface PythonServerConfig {
  pythonExecutable: string;
  serverScript: string;
  port: number;
  healthCheckEndpoint: string;
  startupTimeout: number;
  userDataBaseDirectory: string;
  isDevelopment: boolean;
}

// Re-export shared types for convenience
export type {
  PythonServerState,
  PythonServerStatus,
  PythonServerResult,
} from '../../shared/types/python-server';
