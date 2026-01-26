export interface PythonServerConfig {
  pythonExecutable: string;
  serverScript: string;
  port: number;
  healthCheckEndpoint: string;
  startupTimeout: number;
}

export interface PythonServerState {
  pid: number;
  port: number;
  startedAt: string;
  pythonExecutable: string;
  serverScriptPath: string;
}

export interface PythonServerStatus {
  isRunning: boolean;
  pid?: number;
  port?: number;
  startedAt?: string;
  error?: string;
}

export interface PythonServerResult<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
}
