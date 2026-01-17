/**
 * Appends a suffix to a GitHub username if not already present.
 * 
 * This function ensures usernames follow a consistent format by adding
 * a required suffix (e.g., "_LinkedIn") if it's not already there.
 * 
 * @param username - The base GitHub username to process
 * @param suffix - The required suffix to append (e.g., "_LinkedIn")
 * @returns The username with the suffix appended
 * 
 * @throws {Error} If suffix is empty or whitespace
 * @throws {Error} If username is empty or whitespace
 * @throws {Error} If username contains suffix in the middle (malformed)
 * 
 * @example
 * ```typescript
 * githubUsername("octocat", "_LinkedIn") // "octocat_LinkedIn"
 * githubUsername("octocat_LinkedIn", "_LinkedIn") // "octocat_LinkedIn" (already has suffix)
 * githubUsername("octo_LinkedIn_cat", "_LinkedIn") // throws (suffix in middle)
 * ```
 */
export const githubUsername = (username: string, suffix: string): string => {
    // Validate suffix
    const trimmedSuffix = suffix.trim();
    if (!trimmedSuffix) {
        throw new Error('Suffix is required and cannot be empty');
    }

    // Validate username
    const trimmedUsername = username.trim();
    if (!trimmedUsername) {
        throw new Error('Username is required and cannot be empty');
    }

    // If username already ends with suffix, return as-is
    if (trimmedUsername.endsWith(trimmedSuffix)) {
        return trimmedUsername;
    }

    // Check if suffix appears in the middle (likely malformed)
    if (trimmedUsername.includes(trimmedSuffix)) {
        throw new Error(
            `Username "${trimmedUsername}" contains suffix "${trimmedSuffix}" in an incorrect position. ` +
            `Suffix must only appear at the end.`
        );
    }

    // Append suffix
    return `${trimmedUsername}_${trimmedSuffix}`;
};
