/**
 * Settings file management with atomic writes and error recovery
 */

import { app } from 'electron';
import * as fs from 'node:fs/promises';
import * as path from 'node:path';
import { getLogger } from '@libs/shared/utils/logger';
import { isDevelopment } from '@libs/shared/utils/env';
import type { AppSettings, SettingsResult } from './types/settings';
import { DEFAULT_SETTINGS } from './types/settings';

const log = getLogger({ name: 'settings' });

/**
 * Get settings file path based on environment
 */
function getSettingsPath(): string {
  const userDataPath = app.getPath('userData');
  const fileName = isDevelopment() ? 'settings.dev.json' : 'settings.json';
  return path.join(userDataPath, fileName);
}

/**
 * Get backup file path for corrupt settings
 */
function getBackupPath(): string {
  const settingsPath = getSettingsPath();
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  return `${settingsPath}.backup-${timestamp}`;
}

/**
 * Read settings from file
 * Returns default settings on first run or parse errors
 */
export async function getSettings(): Promise<SettingsResult<AppSettings>> {
  const settingsPath = getSettingsPath();

  try {
    // Check if file exists
    try {
      await fs.access(settingsPath);
    } catch {
      // File doesn't exist - first run
      log.info('Settings file not found, returning defaults');
      return { success: true, data: DEFAULT_SETTINGS };
    }

    // Read and parse file
    const content = await fs.readFile(settingsPath, 'utf-8');
    const settings = JSON.parse(content) as AppSettings;

    log.info('Settings loaded successfully');
    return { success: true, data: settings };
  } catch (error) {
    // Handle parse errors
    if (error instanceof SyntaxError) {
      log.error({ error }, 'Settings file is corrupt, backing up and returning defaults');

      // Backup corrupt file
      try {
        const backupPath = getBackupPath();
        await fs.copyFile(settingsPath, backupPath);
        log.info({ backupPath }, 'Corrupt settings backed up');
      } catch (backupError) {
        log.error({ error: backupError }, 'Failed to backup corrupt settings');
      }

      // Return defaults
      return { success: true, data: DEFAULT_SETTINGS };
    }

    // Other errors
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    log.error({ error: errorMessage }, 'Failed to read settings');
    return { success: false, error: `Failed to read settings: ${errorMessage}` };
  }
}

/**
 * Save settings to file with atomic write
 * Uses temp file + rename for atomic operation
 */
export async function saveSettings(settings: AppSettings): Promise<SettingsResult<void>> {
  const settingsPath = getSettingsPath();
  const tempPath = `${settingsPath}.tmp`;

  try {
    // Ensure userData directory exists
    const userDataPath = app.getPath('userData');
    await fs.mkdir(userDataPath, { recursive: true });

    // Write to temp file with pretty formatting
    const content = JSON.stringify(settings, null, 2);
    await fs.writeFile(tempPath, content, 'utf-8');

    // Atomic rename (overwrites existing file)
    await fs.rename(tempPath, settingsPath);

    log.info({ path: settingsPath }, 'Settings saved successfully');
    return { success: true, data: undefined };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    log.error({ error: errorMessage }, 'Failed to save settings');

    // Clean up temp file if it exists
    try {
      await fs.unlink(tempPath);
    } catch {
      // Ignore cleanup errors
    }

    return { success: false, error: `Failed to save settings: ${errorMessage}` };
  }
}

/**
 * Update settings with partial data (merges with existing)
 */
export async function updateSettings(
  partial: Partial<AppSettings>
): Promise<SettingsResult<void>> {
  try {
    // Get current settings
    const result = await getSettings();
    if (!result.success) {
      return result;
    }

    // Deep merge partial settings
    const updated: AppSettings = {
      ...result.data,
      ...partial,
      user: {
        ...result.data.user,
        ...(partial.user || {}),
      },
      integrations: {
        ...result.data.integrations,
        github: {
          ...result.data.integrations.github,
          ...(partial.integrations?.github || {}),
        },
      },
    };

    // Save merged settings
    return await saveSettings(updated);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    log.error({ error: errorMessage }, 'Failed to update settings');
    return { success: false, error: `Failed to update settings: ${errorMessage}` };
  }
}
