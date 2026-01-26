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

// Python server types imported from shared location
import type {
  PythonServerStatus,
  PythonServerState,
  PythonServerResult,
} from '../../shared/types/python-server';

// Re-export for external consumers
export type {
  PythonServerStatus,
  PythonServerState,
  PythonServerResult,
};

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
