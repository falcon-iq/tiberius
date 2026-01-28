import { app, BrowserWindow, ipcMain, dialog } from 'electron';
import path from 'node:path';
import started from 'electron-squirrel-startup';
import { initDatabase, getUsers, addUser, deleteUser, getGoals, addGoal, deleteGoal, updateGoal, closeDatabase, type AddUserInput, type AddGoalInput, type UpdateGoalInput } from './database';
import { initPythonServer, getPythonServerStatus, restartPythonServer } from './python-server';
import { getSettings, saveSettings, updateSettings } from './settings';
import { getLogger } from '@libs/shared/utils/logger';
import { isDevelopment } from '@libs/shared/utils/env';
import type { AppSettings } from './types/settings';

const log = getLogger({ name: 'main' });

// Handle creating/removing shortcuts on Windows when installing/uninstalling.
if (started) {
  app.quit();
}

/**
 * Get Python executable path (virtual env in development, bundled in production)
 */
function getPythonExecutable(): string {
  const isDev = isDevelopment();

  if (isDev) {
    // Development: use virtual environment
    const venvPath = path.join(process.cwd(), '.venv');

    if (process.platform === 'win32') {
      return path.join(venvPath, 'Scripts', 'python.exe');
    } else {
      return path.join(venvPath, 'bin', 'python3');
    }
  }

  // Production: use bundled Python
  const resourcesPath = process.resourcesPath || path.join(__dirname, '..', '..');
  const platform = process.platform;

  if (platform === 'darwin' || platform === 'linux') {
    return path.join(resourcesPath, 'python-runtime', 'bin', 'python3');
  } else if (platform === 'win32') {
    return path.join(resourcesPath, 'python-runtime', 'python.exe');
  }

  throw new Error(`Unsupported platform: ${platform}`);
}

/**
 * Get Python server script path (source in dev, bundled in production)
 */
function getPythonServerScript(): string {
  const isDev = isDevelopment();

  if (isDev) {
    // Development: use source path relative to cwd
    return path.join(process.cwd(), 'src', 'python', 'server.py');
  }

  // Production: use bundled path in resources
  const resourcesPath = process.resourcesPath || path.join(__dirname, '..', '..');
  return path.join(resourcesPath, 'src', 'python', 'server.py');
}

const createWindow = () => {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  // and load the index.html of the app.
  if (MAIN_WINDOW_VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(MAIN_WINDOW_VITE_DEV_SERVER_URL);
    // Open the DevTools in development mode.
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(
      path.join(__dirname, `../renderer/${MAIN_WINDOW_VITE_NAME}/index.html`),
    );
  }
};

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', async () => {
  initDatabase();

  // Start Python server (non-blocking)
  try {
    const pythonExecutable = getPythonExecutable();
    const serverScript = getPythonServerScript();

    const result = await initPythonServer({
      pythonExecutable,
      serverScript,
      port: 8765,
      healthCheckEndpoint: '/health',
      startupTimeout: 10000,
      userDataPath: app.getPath('userData'),
    });

    if (!result.success) {
      log.error({ error: result.error }, 'Python server failed to start');
      // Show notification but continue
      dialog.showErrorBox(
        'Python Server Error',
        'Background services unavailable. Some features may be limited.'
      );
    } else {
      log.info({ pid: result.data?.pid }, 'Python server started');
    }
  } catch (error) {
    log.error({ error }, 'Python server init error');
  }

  createWindow();
});

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  // On OS X it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// IPC handlers for database operations
ipcMain.handle('db:getUsers', () => getUsers());
ipcMain.handle('db:addUser', (_event, user: AddUserInput) => addUser(user));
ipcMain.handle('db:deleteUser', (_event, id: number) => deleteUser(id));

ipcMain.handle('db:getGoals', () => getGoals());
ipcMain.handle('db:addGoal', (_event, goal: AddGoalInput) => addGoal(goal));
ipcMain.handle('db:deleteGoal', (_event, id: number) => deleteGoal(id));
ipcMain.handle('db:updateGoal', (_event, goal: UpdateGoalInput) => updateGoal(goal));

// IPC handlers for Python server operations
ipcMain.handle('python:getStatus', () => getPythonServerStatus());
ipcMain.handle('python:restart', () => restartPythonServer());

// IPC handlers for settings operations
ipcMain.handle('settings:get', () => getSettings());
ipcMain.handle('settings:save', (_event, settings: AppSettings) => saveSettings(settings));
ipcMain.handle('settings:update', (_event, partial: Partial<AppSettings>) => updateSettings(partial));

// Clean up database on app quit
app.on('before-quit', () => {
  closeDatabase();
});
