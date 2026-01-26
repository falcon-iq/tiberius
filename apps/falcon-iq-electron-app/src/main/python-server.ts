import { spawn } from 'node:child_process';
import http from 'node:http';
import { getLogger } from '@libs/shared/utils/logger';
import {
  savePythonServerState,
  getPythonServerState,
  clearPythonServerState,
} from './database';
import type {
  PythonServerConfig,
  PythonServerState,
  PythonServerStatus,
  PythonServerResult,
} from './types/python-server';

const log = getLogger({ name: 'python-server' });

let currentConfig: PythonServerConfig | null = null;

/**
 * Check if a process is running by PID
 */
function isProcessRunning(pid: number): boolean {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

/**
 * Kill a process by PID
 */
async function killProcess(pid: number): Promise<boolean> {
  try {
    if (!isProcessRunning(pid)) {
      log.info({ pid }, 'Process already dead');
      return true;
    }

    log.info({ pid }, 'Killing process');
    process.kill(pid, 'SIGTERM');

    // Wait for process to die with async polling
    const startTime = Date.now();
    const pollInterval = 100; // Check every 100ms
    const timeout = 5000; // Wait up to 5 seconds

    while (isProcessRunning(pid) && Date.now() - startTime < timeout) {
      await new Promise((resolve) => setTimeout(resolve, pollInterval));
    }

    // Force kill if still running
    if (isProcessRunning(pid)) {
      log.warn({ pid }, 'Process did not die, force killing');
      process.kill(pid, 'SIGKILL');
    }

    return !isProcessRunning(pid);
  } catch (error) {
    log.error({ error, pid }, 'Failed to kill process');
    return false;
  }
}

/**
 * Kill existing server from database state
 */
async function killExistingServer(): Promise<PythonServerResult<void>> {
  const stateResult = getPythonServerState();

  if (!stateResult.success) {
    return { success: false, error: stateResult.error };
  }

  if (!stateResult.data) {
    log.info('No existing server state found');
    return { success: true };
  }

  const { pid } = stateResult.data;
  log.info({ pid }, 'Found existing server PID');

  const killed = await killProcess(pid);

  if (!killed) {
    return { success: false, error: `Failed to kill process ${pid}` };
  }

  const clearResult = clearPythonServerState();
  if (!clearResult.success) {
    return { success: false, error: clearResult.error };
  }

  log.info({ pid }, 'Killed existing server');
  return { success: true };
}

/**
 * Perform health check on server
 */
function healthCheck(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const req = http.get(`http://127.0.0.1:${port}/health`, (res) => {
      resolve(res.statusCode === 200);
    });

    req.on('error', () => {
      resolve(false);
    });

    req.setTimeout(1000, () => {
      req.destroy();
      resolve(false);
    });
  });
}

/**
 * Wait for server to become ready
 */
async function waitForServerReady(
  port: number,
  timeout: number
): Promise<boolean> {
  const startTime = Date.now();
  const pollInterval = 100;

  while (Date.now() - startTime < timeout) {
    const isHealthy = await healthCheck(port);
    if (isHealthy) {
      return true;
    }
    await new Promise((resolve) => setTimeout(resolve, pollInterval));
  }

  return false;
}

/**
 * Spawn Python server process
 */
async function spawnPythonServer(
  config: PythonServerConfig
): Promise<PythonServerResult<PythonServerState>> {
  log.info(
    { pythonExecutable: config.pythonExecutable, port: config.port },
    'Spawning Python server'
  );

  try {
    const child = spawn(
      config.pythonExecutable,
      [config.serverScript, config.port.toString()],
      {
        detached: true,
        stdio: ['ignore', 'pipe', 'pipe'],
        windowsHide: true,
      }
    );

    // Log stdout/stderr
    child.stdout?.on('data', (data) => {
      log.info({ output: data.toString().trim() }, 'Python server stdout');
    });

    child.stderr?.on('data', (data) => {
      log.info({ output: data.toString().trim() }, 'Python server stderr');
    });

    child.on('error', (error) => {
      log.error({ error }, 'Python server process error');
    });

    child.on('exit', (code, signal) => {
      log.info({ code, signal }, 'Python server process exited');
    });

    // Unref so it doesn't keep parent alive
    child.unref();

    // Wait for server to be ready
    const isReady = await waitForServerReady(
      config.port,
      config.startupTimeout
    );

    if (!isReady) {
      if (child.pid) {
        await killProcess(child.pid);
      }
      return {
        success: false,
        error: `Server failed to start within ${config.startupTimeout}ms`,
      };
    }

    if (!child.pid) {
      return {
        success: false,
        error: 'Failed to get process PID',
      };
    }

    const state: PythonServerState = {
      pid: child.pid,
      port: config.port,
      startedAt: new Date().toISOString(),
      pythonExecutable: config.pythonExecutable,
      serverScriptPath: config.serverScript,
    };

    const saveResult = savePythonServerState(state);
    if (!saveResult.success) {
      await killProcess(child.pid);
      return { success: false, error: saveResult.error };
    }

    log.info({ pid: child.pid, port: config.port }, 'Python server started');
    return { success: true, data: state };
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : 'Unknown error';
    log.error({ error }, 'Failed to spawn Python server');
    return { success: false, error: errorMessage };
  }
}

/**
 * Initialize Python server on app startup
 */
export async function initPythonServer(
  config: PythonServerConfig
): Promise<PythonServerResult<PythonServerState>> {
  currentConfig = config;

  // Kill any existing server
  const killResult = await killExistingServer();
  if (!killResult.success) {
    log.warn({ error: killResult.error }, 'Failed to kill existing server');
    // Continue anyway - try to start new server
  }

  // Spawn new server
  return spawnPythonServer(config);
}

/**
 * Get current Python server status
 */
export async function getPythonServerStatus(): Promise<PythonServerStatus> {
  const stateResult = getPythonServerState();

  if (!stateResult.success) {
    return {
      isRunning: false,
      error: stateResult.error,
    };
  }

  if (!stateResult.data) {
    return {
      isRunning: false,
    };
  }

  const { pid, port, startedAt } = stateResult.data;

  // Check if process is still running
  if (!isProcessRunning(pid)) {
    return {
      isRunning: false,
      error: 'Process not running',
    };
  }

  // Verify health
  const isHealthy = await healthCheck(port);
  if (!isHealthy) {
    return {
      isRunning: false,
      pid,
      error: 'Health check failed',
    };
  }

  return {
    isRunning: true,
    pid,
    port,
    startedAt,
  };
}

/**
 * Restart Python server
 */
export async function restartPythonServer(): Promise<
  PythonServerResult<PythonServerState>
> {
  if (!currentConfig) {
    return { success: false, error: 'Server not initialized' };
  }

  log.info('Restarting Python server');

  const killResult = await killExistingServer();
  if (!killResult.success) {
    return { success: false, error: killResult.error };
  }

  return spawnPythonServer(currentConfig);
}
