/**
 * User display utilities for consistent username and name formatting across the app.
 * Handles EMU suffix stripping, display names, and initials generation.
 */

/**
 * User data shape with optional fields
 */
export interface UserDisplayData {
  username: string;
  firstname?: string | null;
  lastname?: string | null;
  github_suffix?: string | null;
}

/**
 * Strip EMU suffix from username for display purposes.
 * Uses the stored github_suffix value when available for accuracy,
 * or falls back to parsing the suffix from the username.
 *
 * @param username - Full GitHub username (e.g., "bsteyn_LinkedIn")
 * @param githubSuffix - Optional stored EMU suffix (e.g., "LinkedIn")
 * @returns Username without EMU suffix (e.g., "bsteyn")
 *
 * @example
 * ```typescript
 * stripEmuSuffix("bsteyn_LinkedIn", "LinkedIn") // "bsteyn"
 * stripEmuSuffix("john_doe_LinkedIn", "LinkedIn") // "john_doe"
 * stripEmuSuffix("regularuser") // "regularuser"
 * ```
 */
export function stripEmuSuffix(username: string, githubSuffix?: string | null): string {
  if (!githubSuffix) {
    return username;
  }

  const suffixWithUnderscore = `_${githubSuffix}`;
  if (username.endsWith(suffixWithUnderscore)) {
    return username.slice(0, -suffixWithUnderscore.length);
  }

  return username;
}

/**
 * Generate display name from user data.
 * Priority: "Firstname Lastname" -> Firstname -> Lastname -> Username (with EMU suffix stripped if present)
 *
 * @param user - User data object
 * @returns Display name suitable for UI presentation
 *
 * @example
 * ```typescript
 * getDisplayName({ firstname: "John", lastname: "Doe", username: "jdoe_LinkedIn" })
 * // "John Doe"
 *
 * getDisplayName({ firstname: "John", username: "john_LinkedIn", github_suffix: "LinkedIn" })
 * // "John"
 *
 * getDisplayName({ username: "bsteyn_LinkedIn", github_suffix: "LinkedIn" })
 * // "bsteyn"
 * ```
 */
export function getDisplayName(user: UserDisplayData): string {
  // Priority 1: "Firstname Lastname"
  if (user.firstname && user.lastname) {
    return `${user.firstname} ${user.lastname}`;
  }

  // Priority 2: Just firstname
  if (user.firstname) {
    return user.firstname;
  }

  // Priority 3: Just lastname
  if (user.lastname) {
    return user.lastname;
  }

  // Priority 4: Username (stripped of EMU suffix if present)
  return stripEmuSuffix(user.username, user.github_suffix);
}

/**
 * Generate initials from user data.
 * Priority: First+Last initials -> First name (2 chars) -> Last name (2 chars) -> Username (2 chars, EMU suffix stripped if present)
 *
 * @param user - User data object
 * @returns Two-character initials in uppercase
 *
 * @example
 * ```typescript
 * getInitials({ firstname: "John", lastname: "Doe", username: "jdoe" })
 * // "JD"
 *
 * getInitials({ firstname: "Alice", username: "alice_LinkedIn" })
 * // "AL"
 *
 * getInitials({ username: "bsteyn_LinkedIn", github_suffix: "LinkedIn" })
 * // "BS"
 * ```
 */
export function getInitials(user: UserDisplayData): string {
  // Priority 1: Use firstname + lastname
  if (user.firstname && user.lastname) {
    return (user.firstname[0] + user.lastname[0]).toUpperCase();
  }

  // Priority 2: Use firstname only (take first two letters)
  if (user.firstname && user.firstname.length >= 2) {
    return user.firstname.slice(0, 2).toUpperCase();
  }

  // Priority 3: Use lastname only (take first two letters)
  if (user.lastname && user.lastname.length >= 2) {
    return user.lastname.slice(0, 2).toUpperCase();
  }

  // Priority 4: Fallback to username (take first two letters, strip EMU suffix if present)
  const usernameWithoutSuffix = stripEmuSuffix(user.username, user.github_suffix);
  return usernameWithoutSuffix.slice(0, 2).toUpperCase();
}
