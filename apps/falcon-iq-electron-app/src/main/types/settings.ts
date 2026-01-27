/**
 * Main process-specific settings types.
 * Settings are persisted to settings.json in app userData directory.
 */

/**
 * Application settings schema
 */
export interface AppSettings {
  /** Schema version for migration support */
  version: string;

  /** Current user details */
  user: {
    firstName: string;
    lastName: string;
    ldapUsername: string;
  };

  /** External integrations configuration */
  integrations: {
    github: {
      /** GitHub Personal Access Token */
      pat: string;
      /** GitHub EMU suffix (if detected) */
      emuSuffix?: string;
      /** Full GitHub username (with EMU suffix if applicable) */
      username?: string;
    };
  };

  /** Whether onboarding wizard has been completed */
  onboardingCompleted: boolean;
}

/**
 * Default settings for new installations
 */
export const DEFAULT_SETTINGS: AppSettings = {
  version: '1.0.0',
  user: {
    firstName: '',
    lastName: '',
    ldapUsername: '',
  },
  integrations: {
    github: {
      pat: '',
    },
  },
  onboardingCompleted: false,
};

/**
 * Result type for settings operations
 */
export type SettingsResult<T> =
  | { success: true; data: T }
  | { success: false; error: string };
