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
