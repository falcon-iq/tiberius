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

export interface ElectronAPI {
  getUsers(): Promise<DatabaseResult<User[]>>;
  addUser(user: AddUserInput): Promise<DatabaseResult<User>>;
  deleteUser(id: number): Promise<DatabaseResult<void>>;
}

declare global {
  interface Window {
    api: ElectronAPI;
  }
}
