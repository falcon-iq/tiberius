import { contextBridge, ipcRenderer } from 'electron';

export interface AddUserInput {
  username: string;
  github_suffix?: string | null;
  email_address?: string | null;
  firstname?: string | null;
  lastname?: string | null;
}

contextBridge.exposeInMainWorld('api', {
  getUsers: () => ipcRenderer.invoke('db:getUsers'),
  addUser: (user: AddUserInput) => ipcRenderer.invoke('db:addUser', user),
  deleteUser: (id: number) => ipcRenderer.invoke('db:deleteUser', id),
});
