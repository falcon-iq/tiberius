# GitHub Token Validation

This module provides utilities to validate GitHub Personal Access Tokens (PATs) and check their permissions.

## Features

- ✅ Validate if a GitHub PAT is valid and active
- ✅ Retrieve the username associated with the token
- ✅ Check token scopes/permissions
- ✅ Verify if specific permissions are present

## Installation

This is part of the `@tiberius/integrations-github` package and is automatically available when you import from it.

## Usage

### Basic Token Validation

```typescript
import { validateGitHubToken } from '@tiberius/integrations-github';

const result = await validateGitHubToken('ghp_xxx...');

if (result.valid) {
  console.log(`✓ Valid token for user: ${result.username}`);
  console.log(`  Scopes: ${result.scopes?.join(', ')}`);
} else {
  console.log(`✗ Invalid token: ${result.error}`);
}
```

### Check Specific Permissions

```typescript
import { checkTokenScopes } from '@tiberius/integrations-github';

const result = await checkTokenScopes('ghp_xxx...', ['repo', 'read:org']);

if (result.valid && result.hasRequiredScopes) {
  console.log('✓ Token has all required permissions');
} else if (result.valid) {
  console.log(`✗ Missing scopes: ${result.missingScopes?.join(', ')}`);
} else {
  console.log(`✗ Invalid token: ${result.error}`);
}
```

## API Reference

### `validateGitHubToken(token: string): Promise<ValidateTokenResult>`

Validates a GitHub PAT by attempting to authenticate and fetch user information.

**Parameters:**
- `token` - The GitHub Personal Access Token to validate

**Returns:** `Promise<ValidateTokenResult>`
- `valid` - Boolean indicating if the token is valid
- `username` - GitHub username (only present if valid)
- `scopes` - Array of permission scopes (only present if valid)
- `error` - Error message (only present if invalid)

**Example:**
```typescript
const result = await validateGitHubToken('ghp_xxx...');
```

### `checkTokenScopes(token: string, requiredScopes: string[]): Promise<ValidateTokenResult & {...}>`

Validates a token and checks if it has specific required scopes.

**Parameters:**
- `token` - The GitHub Personal Access Token to validate
- `requiredScopes` - Array of required scope names (e.g., `['repo', 'read:org']`)

**Returns:** `Promise<ValidateTokenResult & { hasRequiredScopes?, missingScopes? }>`
- All fields from `ValidateTokenResult`
- `hasRequiredScopes` - Boolean indicating if all required scopes are present
- `missingScopes` - Array of missing scope names (only present if some are missing)

**Example:**
```typescript
const result = await checkTokenScopes('ghp_xxx...', ['repo']);
if (result.hasRequiredScopes) {
  // Token has the 'repo' scope
}
```

## Common GitHub Token Scopes

- `repo` - Full control of private repositories
- `public_repo` - Access public repositories
- `read:org` - Read org and team membership
- `write:org` - Read and write org and team membership
- `admin:org` - Full control of orgs and teams
- `user` - Read and write user profile data
- `read:user` - Read user profile data

## Testing

You can test token validation using the provided test script:

```bash
# Using the test script directly
npx tsx tools/scripts/test-github-token.ts YOUR_GITHUB_TOKEN

# Or with environment variable
GITHUB_TOKEN=ghp_xxx... npx tsx tools/scripts/test-github-token.ts
```

## Error Handling

The validation functions never throw errors. Instead, they return a result object with `valid: false` and an `error` message:

- **401 Unauthorized**: Invalid or expired token
- **403 Forbidden**: Valid token but insufficient permissions or rate limit exceeded
- **Network errors**: Connection issues or other problems

**Example:**
```typescript
const result = await validateGitHubToken(token);

if (!result.valid) {
  switch (result.error) {
    case 'Invalid or expired token - authentication failed':
      // Handle invalid token
      break;
    case 'Token is valid but has insufficient permissions or rate limit exceeded':
      // Handle permission/rate limit issues
      break;
    default:
      // Handle other errors
      break;
  }
}
```

## Implementation Details

- Uses Octokit's `GET /user` endpoint for validation
- Works with all PAT permission scopes (even minimal ones)
- Lightweight and fast (single API call)
- Extracts token scopes from response headers when available
- No plugins loaded for faster validation
