// libs/integrations/github/src/lib/auth.ts
//
// GitHub Personal Access Token (PAT) validation utilities

import { Octokit } from 'octokit';

/**
 * Result of GitHub token validation
 */
export interface ValidateTokenResult {
    /** Whether the token is valid */
    valid: boolean;
    /** GitHub username associated with the token (only present if valid) */
    username?: string;
    /** Error message if validation failed */
    error?: string;
    /** Token scopes/permissions (only present if valid) */
    scopes?: string[];
}

/**
 * Result of GitHub user validation
 */
export interface ValidateUserResult {
    /** Whether the user exists */
    valid: boolean;
    /** The validated username (case-corrected) */
    username?: string;
    /** Error message if validation failed */
    error?: string;
    /** User details if found */
    user?: {
        /** GitHub username (login) */
        login: string;
        /** Unique user ID */
        id: number;
        /** Display name */
        name: string | null;
        /** Public email */
        email: string | null;
        /** Avatar/profile picture URL */
        avatar_url: string;
        /** Account type: 'User' or 'Organization' */
        type: string;
    };
}

/**
 * Validates a GitHub Personal Access Token (PAT) by attempting to authenticate
 * and fetch the authenticated user's information.
 *
 * Uses the GET /user endpoint which works with all PAT permission scopes.
 *
 * @param token - The GitHub PAT to validate
 * @returns Promise resolving to validation result with user info if valid
 *
 * @example
 * ```typescript
 * const result = await validateGitHubToken('ghp_xxx...');
 *
 * if (result.valid) {
 *   console.log(`✓ Valid token for user: ${result.username}`);
 *   console.log(`  Scopes: ${result.scopes?.join(', ')}`);
 * } else {
 *   console.log(`✗ Invalid token: ${result.error}`);
 * }
 * ```
 */
export async function validateGitHubToken(
    token: string
): Promise<ValidateTokenResult> {
    // Basic input validation
    if (!token || token.trim().length === 0) {
        return {
            valid: false,
            error: 'Token is required and cannot be empty',
        };
    }

    try {
        // Create a basic Octokit instance without plugins for faster validation
        const octokit = new Octokit({ auth: token.trim() });

        // GET /user is the standard way to validate a token
        // This endpoint works with minimal permissions and returns user info
        const response = await octokit.rest.users.getAuthenticated();

        // Extract token scopes from response headers (if available)
        const scopesHeader = response.headers['x-oauth-scopes'];
        const scopes = scopesHeader
            ? scopesHeader.split(',').map((s) => s.trim()).filter(Boolean)
            : undefined;

        return {
            valid: true,
            username: response.data.login,
            scopes,
        };
    } catch (error: unknown) {
        // Handle different error types
        const err = error as { status?: number; message?: string };

        if (err.status === 401) {
            return {
                valid: false,
                error: 'Invalid or expired token - authentication failed',
            };
        }

        if (err.status === 403) {
            return {
                valid: false,
                error: 'Token is valid but has insufficient permissions or rate limit exceeded',
            };
        }

        // Network or other errors
        return {
            valid: false,
            error: err.message || 'Unknown error occurred during validation',
        };
    }
}

/**
 * Checks if a GitHub token has specific required scopes/permissions.
 *
 * @param token - The GitHub PAT to check
 * @param requiredScopes - Array of scope names that must be present (e.g., ['repo', 'read:org'])
 * @returns Promise resolving to result indicating if all required scopes are present
 *
 * @example
 * ```typescript
 * const result = await checkTokenScopes('ghp_xxx...', ['repo', 'read:org']);
 *
 * if (result.valid && result.hasRequiredScopes) {
 *   console.log('✓ Token has all required permissions');
 * } else if (result.valid) {
 *   console.log(`✗ Missing scopes: ${result.missingScopes?.join(', ')}`);
 * }
 * ```
 */
export async function checkTokenScopes(
    token: string,
    requiredScopes: string[]
): Promise<
    ValidateTokenResult & {
        hasRequiredScopes?: boolean;
        missingScopes?: string[];
    }
> {
    const validationResult = await validateGitHubToken(token);

    if (!validationResult.valid) {
        return validationResult;
    }

    const tokenScopes = validationResult.scopes || [];
    const missingScopes = requiredScopes.filter(
        (required) => !tokenScopes.includes(required)
    );

    return {
        ...validationResult,
        hasRequiredScopes: missingScopes.length === 0,
        missingScopes: missingScopes.length > 0 ? missingScopes : undefined,
    };
}

/**
 * Validates if a GitHub username exists on the GitHub platform.
 *
 * Uses the GET /users/{username} endpoint which does not require special token scopes.
 * This is useful for validating team member usernames before adding them to lists or teams.
 *
 * @param token - A valid GitHub PAT for authentication
 * @param username - The GitHub username to validate
 * @returns Promise resolving to validation result with user details if found
 *
 * @example
 * ```typescript
 * const result = await validateGitHubUser('ghp_xxx...', 'octocat');
 *
 * if (result.valid) {
 *   console.log(`✓ User found: ${result.user?.login}`);
 *   console.log(`  Name: ${result.user?.name}`);
 *   console.log(`  Type: ${result.user?.type}`);
 * } else {
 *   console.log(`✗ User not found: ${result.error}`);
 * }
 * ```
 */
export async function validateGitHubUser(
    token: string,
    username: string
): Promise<ValidateUserResult> {
    // Basic input validation
    if (!username || username.trim().length === 0) {
        return {
            valid: false,
            error: 'Username is required and cannot be empty',
        };
    }

    if (!token || token.trim().length === 0) {
        return {
            valid: false,
            error: 'Token is required and cannot be empty',
        };
    }


    try {
        // Create a basic Octokit instance
        const octokit = new Octokit({ auth: token.trim() });

        // GET /users/{username} - works with any PAT, no special scopes required
        const response = await octokit.rest.users.getByUsername({
            username: username.trim(),
        });

        return {
            valid: true,
            username: response.data.login,
            user: {
                login: response.data.login,
                id: response.data.id,
                name: response.data.name,
                email: response.data.email,
                avatar_url: response.data.avatar_url,
                type: response.data.type,
            },
        };

    } catch (error: unknown) {
        // Handle different error types
        const err = error as { status?: number; message?: string };

        if (err.status === 404) {
            return {
                valid: false,
                error: `User "${username}" not found on GitHub`,
            };
        }

        if (err.status === 401) {
            return {
                valid: false,
                error: 'Invalid or expired token - authentication failed',
            };
        }

        if (err.status === 403) {
            return {
                valid: false,
                error: 'Rate limit exceeded or insufficient permissions',
            };
        }

        // Network or other errors
        return {
            valid: false,
            error: err.message || 'Unknown error occurred during validation',
        };
    }
}
