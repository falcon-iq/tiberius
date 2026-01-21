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
    const trimmedLowercaseUsername = username.trim().toLowerCase();

    // Validate non empty username
    if (!trimmedLowercaseUsername) {
        throw new Error('Username is required and cannot be empty');
    }

    // If username already ends with suffix, return as-is
    if (trimmedLowercaseUsername.endsWith(trimmedSuffix.toLowerCase())) {
        return trimmedLowercaseUsername;
    }

    // Check if suffix appears in the middle (likely malformed)
    if (trimmedLowercaseUsername.includes(trimmedSuffix)) {
        throw new Error(
            `Username "${trimmedLowercaseUsername}" contains suffix "${trimmedSuffix}" in an incorrect position. ` +
            `Suffix must only appear at the end.`
        );
    }

    // Append suffix
    return `${trimmedLowercaseUsername}_${trimmedSuffix}`;
};

/**
 * Parses the suffix from a GitHub username if it is an entrprise managed user (EMU).
 * 
 * @param username - The GitHub username to parse
 * @returns The suffix if it is an entrprise managed user (EMU)
 */
export const parseEmuSuffix = (username: string): string | undefined => {
    const i = username.lastIndexOf('_');
    if (i <= 0 || i === username.length - 1) return undefined;

    const suffix = username.slice(i + 1);

    // Heuristic validation: adjust to your reality
    if (!/^[a-z0-9-]{2,20}$/i.test(suffix)) return undefined;

    return suffix;
};