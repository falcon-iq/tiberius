export interface User {
  id: number;
  username: string;
  github_suffix: string | null;
  email_address: string | null;
  firstname: string | null;
  lastname: string | null;
}

export interface AddUserInput {
  username: string;
  github_suffix?: string | null;
  email_address?: string | null;
  firstname?: string | null;
  lastname?: string | null;
}

export interface DatabaseResult<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface PythonServerStatus {
  isRunning: boolean;
  pid?: number;
  port?: number;
  startedAt?: string;
  error?: string;
}

export interface PythonServerState {
  pid: number;
  port: number;
  startedAt: string;
  pythonExecutable: string;
  serverScriptPath: string;
}

export interface PythonServerResult<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface ElectronAPI {
  getUsers(): Promise<DatabaseResult<User[]>>;
  addUser(user: AddUserInput): Promise<DatabaseResult<User>>;
  deleteUser(id: number): Promise<DatabaseResult<void>>;
  pythonServer: {
    getStatus(): Promise<PythonServerStatus>;
    restart(): Promise<PythonServerResult<PythonServerState>>;
  };
}

declare global {
  interface Window {
    api: ElectronAPI;
  }
}
