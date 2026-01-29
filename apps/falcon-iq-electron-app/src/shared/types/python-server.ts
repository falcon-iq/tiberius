/**
 * Shared Python server types used across main and renderer processes.
 * These types define the IPC contract for Python server operations.
 */

/**
 * Python server runtime state (persisted in .falcon/python-server.json).
 */
export interface PythonServerState {
  pid: number;
  port: number;
  startedAt: string;
  pythonExecutable: string;
  serverScriptPath: string;
}

/**
 * Python server status returned to renderer via IPC.
 */
export interface PythonServerStatus {
  isRunning: boolean;
  pid?: number;
  port?: number;
  startedAt?: string;
  error?: string;
}

/**
 * Generic result wrapper for Python server operations.
 */
export interface PythonServerResult<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
}
