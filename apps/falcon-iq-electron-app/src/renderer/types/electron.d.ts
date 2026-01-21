export interface GithubUser {
  id: number;
  username: string;
}

export interface DatabaseResult<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface ElectronAPI {
  getGithubUsers(): Promise<DatabaseResult<GithubUser[]>>;
  addGithubUser(username: string): Promise<DatabaseResult<GithubUser>>;
  deleteGithubUser(id: number): Promise<DatabaseResult<void>>;
}

declare global {
  interface Window {
    api: ElectronAPI;
  }
}
