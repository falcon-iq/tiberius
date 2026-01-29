/**
 * Python server state file management with atomic writes and error recovery.
 * Uses synchronous file operations for API compatibility with existing database code.
 */

import { app } from 'electron';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { getLogger } from '@libs/shared/utils/logger';
import { isDevelopment } from '@libs/shared/utils/env';
import type { PythonServerState, PythonServerResult } from './types/python-server';

const log = getLogger({ name: 'python-state' });

/**
 * Get state file path based on environment
 */
function getStateFilePath(): string {
  const userDataPath = app.getPath('userData');
  const falconDir = path.join(userDataPath, '.falcon');
  const fileName = isDevelopment() ? 'python-server.dev.json' : 'python-server.json';
  return path.join(falconDir, fileName);
}

/**
 * Ensure .falcon directory exists
 */
function ensureFalconDirectory(): void {
  const userDataPath = app.getPath('userData');
  const falconDir = path.join(userDataPath, '.falcon');
  fs.mkdirSync(falconDir, { recursive: true });
}

/**
 * Get backup file path for corrupt state files
 */
function getBackupPath(): string {
  const statePath = getStateFilePath();
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  return `${statePath}.backup-${timestamp}`;
}

/**
 * Save Python server state to file with atomic write.
 * Uses temp file + rename for atomic operation.
 */
export function savePythonServerState(state: PythonServerState): PythonServerResult<void> {
  const statePath = getStateFilePath();
  const tempPath = `${statePath}.tmp`;

  try {
    // Ensure .falcon directory exists
    ensureFalconDirectory();

    // Write to temp file with pretty formatting
    const content = JSON.stringify(state, null, 2);
    fs.writeFileSync(tempPath, content, 'utf-8');

    // Atomic rename (overwrites existing file)
    fs.renameSync(tempPath, statePath);

    log.info({ path: statePath, pid: state.pid, port: state.port }, 'Python server state saved');
    return { success: true, data: undefined };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    log.error({ error: errorMessage }, 'Failed to save Python server state');

    // Clean up temp file if it exists
    try {
      fs.unlinkSync(tempPath);
    } catch {
      // Ignore cleanup errors
    }

    return { success: false, error: `Failed to save state: ${errorMessage}` };
  }
}

/**
 * Read Python server state from file.
 * Returns null on first run or if file doesn't exist.
 * Automatically backs up corrupt files.
 */
export function getPythonServerState(): PythonServerResult<PythonServerState | null> {
  const statePath = getStateFilePath();

  try {
    // Check if file exists
    try {
      fs.accessSync(statePath);
    } catch {
      log.info('Python server state file not found, returning null');
      return { success: true, data: null };
    }

    // Read and parse file
    const content = fs.readFileSync(statePath, 'utf-8');
    const state = JSON.parse(content) as PythonServerState;

    log.info({ pid: state.pid, port: state.port }, 'Python server state loaded');
    return { success: true, data: state };
  } catch (error) {
    // Handle corrupt JSON file
    if (error instanceof SyntaxError) {
      log.error({ error }, 'State file corrupt, backing up and returning null');

      // Backup corrupt file
      try {
        const backupPath = getBackupPath();
        fs.copyFileSync(statePath, backupPath);
        log.info({ backupPath }, 'Corrupt state backed up');
      } catch (backupError) {
        log.error({ error: backupError }, 'Failed to backup corrupt state');
      }

      // Return null so server can restart cleanly
      return { success: true, data: null };
    }

    // Other errors
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    log.error({ error: errorMessage }, 'Failed to read Python server state');
    return { success: false, error: `Failed to read state: ${errorMessage}` };
  }
}

/**
 * Clear Python server state (delete file).
 */
export function clearPythonServerState(): PythonServerResult<void> {
  const statePath = getStateFilePath();

  try {
    // Check if file exists
    try {
      fs.accessSync(statePath);
    } catch {
      log.info('Python server state file does not exist, nothing to clear');
      return { success: true, data: undefined };
    }

    // Delete file
    fs.unlinkSync(statePath);
    log.info({ path: statePath }, 'Python server state cleared');
    return { success: true, data: undefined };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    log.error({ error: errorMessage }, 'Failed to clear Python server state');
    return { success: false, error: `Failed to clear state: ${errorMessage}` };
  }
}
