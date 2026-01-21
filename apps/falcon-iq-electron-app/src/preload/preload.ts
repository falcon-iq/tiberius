import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('api', {
  getGithubUsers: () => ipcRenderer.invoke('db:getGithubUsers'),
  addGithubUser: (username: string) => ipcRenderer.invoke('db:addGithubUser', username),
  deleteGithubUser: (id: number) => ipcRenderer.invoke('db:deleteGithubUser', id),
});
