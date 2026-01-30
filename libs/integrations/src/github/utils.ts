/**
 * Utility functions for GitHub data parsing
 */

import { parseEmuSuffix } from './username';
import type { ValidateUserResult } from './auth';
import { stripEmuSuffix } from '@libs/shared/utils/user-display';

/**
 * Parsed GitHub user data ready for database storage
 */
export interface ParsedGitHubUser {
  /** LDAP username (GitHub username with suffix stripped) */
  username: string;
  /** First name parsed from display name */
  firstname: string;
  /** Last name parsed from display name */
  lastname: string;
  /** Email address (may be empty if not public) */
  email_address: string;
  /** EMU suffix extracted from username (e.g., "LinkedIn") */
  github_suffix: string | null;
  /** GitHub avatar URL */
  avatar_url: string;
}

/**
 * Parse GitHub user data into database-ready format
 *
 * Extracts firstname/lastname from the GitHub display name and parses
 * the EMU suffix from the username.
 *
 * @param validateResult - Result from validateGitHubUser
 * @returns Parsed user data ready for database insertion
 *
 * @example
 * ```typescript
 * const result = await validateGitHubUser(token, "jdoe_LinkedIn");
 * if (result.valid && result.user) {
 *   const parsedUser = parseGitHubUser(result);
 *   // {
 *   //   username: "jdoe",  // LDAP username without suffix
 *   //   firstname: "John",
 *   //   lastname: "Doe",
 *   //   email_address: "john.doe@company.com",
 *   //   github_suffix: "LinkedIn"
 *   // }
 * }
 * ```
 */
export function parseGitHubUser(validateResult: ValidateUserResult): ParsedGitHubUser {
  const user = validateResult.user;

  if (!user) {
    // Return empty data if user not found
    return {
      username: '',
      firstname: '',
      lastname: '',
      email_address: '',
      github_suffix: null,
      avatar_url: '',
    };
  }

  // Parse name into firstname/lastname
  // GitHub name format is typically "FirstName LastName" but can be anything
  const nameParts = (user.name || '').trim().split(/\s+/);
  const firstname = nameParts[0] || '';
  const lastname = nameParts.slice(1).join(' ') || '';

  // Extract EMU suffix from username
  const github_suffix = parseEmuSuffix(user.login) || null;

  // Strip suffix from username to store only LDAP username
  const ldapUsername = github_suffix
    ? stripEmuSuffix(user.login, github_suffix)
    : user.login;

  return {
    username: ldapUsername,  // LDAP username without suffix
    firstname,
    lastname,
    email_address: user.email || '',
    github_suffix,
    avatar_url: user.avatar_url,
  };
}
