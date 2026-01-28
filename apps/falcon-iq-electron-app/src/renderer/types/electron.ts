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

export interface Goal {
  id: number;
  goal: string;
  start_date: string;
  end_date: string | null;
}

export interface AddGoalInput {
  goal: string;
  end_date?: string | null;
}

export interface DatabaseResult<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface AppSettings {
  version: string;
  user: {
    firstName: string;
    lastName: string;
    ldapUsername: string;
  };
  integrations: {
    github: {
      pat: string;
      emuSuffix?: string;
      username?: string;
    };
  };
  onboardingCompleted: boolean;
}

export interface SettingsResult<T> {
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
  getGoals(): Promise<DatabaseResult<Goal[]>>;
  addGoal(goal: AddGoalInput): Promise<DatabaseResult<Goal>>;
  deleteGoal(id: number): Promise<DatabaseResult<void>>;
  pythonServer: {
    getStatus(): Promise<PythonServerStatus>;
    restart(): Promise<PythonServerResult<PythonServerState>>;
  };
  settings: {
    get(): Promise<SettingsResult<AppSettings>>;
    save(settings: AppSettings): Promise<SettingsResult<void>>;
    update(partial: Partial<AppSettings>): Promise<SettingsResult<void>>;
  };
}

declare global {
  interface Window {
    api: ElectronAPI;
  }
}
