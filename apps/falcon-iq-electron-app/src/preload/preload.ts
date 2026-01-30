import { contextBridge, ipcRenderer } from 'electron';

export interface AddUserInput {
  username: string;
  github_suffix?: string | null;
  email_address?: string | null;
  firstname?: string | null;
  lastname?: string | null;
}

export interface AddGoalInput {
  goal: string;
  start_date?: string | null;
  end_date?: string | null;
}

export interface UpdateGoalInput {
  id: number;
  end_date?: string | null;
}

export interface Goal {
  id: number;
  goal: string;
  start_date: string;
  end_date: string | null;
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

contextBridge.exposeInMainWorld('api', {
  getUsers: () => ipcRenderer.invoke('db:getUsers'),
  addUser: (user: AddUserInput) => ipcRenderer.invoke('db:addUser', user),
  deleteUser: (id: number) => ipcRenderer.invoke('db:deleteUser', id),
  getGoals: () => ipcRenderer.invoke('db:getGoals'),
  addGoal: (goal: AddGoalInput) => ipcRenderer.invoke('db:addGoal', goal),
  deleteGoal: (id: number) => ipcRenderer.invoke('db:deleteGoal', id),
  updateGoal: (goal: UpdateGoalInput) => ipcRenderer.invoke('db:updateGoal', goal),
  getPRCommentStats: (username: string) => ipcRenderer.invoke('db:getPRCommentStats', username),
  getPRCommentsByMetric: (username: string, metricType: string) =>
    ipcRenderer.invoke('db:getPRCommentsByMetric', username, metricType),
  python: {
    getStatus: () => ipcRenderer.invoke('python:getStatus'),
    restart: () => ipcRenderer.invoke('python:restart'),
    getPR: (prId: number) => ipcRenderer.invoke('python:getPR', prId),
    getComment: (prId: number, commentId: number) =>
      ipcRenderer.invoke('python:getComment', prId, commentId),
    getPRFiles: (prId: number) => ipcRenderer.invoke('python:getPRFiles', prId),
  },
  pythonServer: {
    getStatus: () => ipcRenderer.invoke('python:getStatus'),
    restart: () => ipcRenderer.invoke('python:restart'),
  },
  settings: {
    get: () => ipcRenderer.invoke('settings:get'),
    save: (settings: AppSettings) => ipcRenderer.invoke('settings:save', settings),
    update: (partial: Partial<AppSettings>) => ipcRenderer.invoke('settings:update', partial),
  },
});
