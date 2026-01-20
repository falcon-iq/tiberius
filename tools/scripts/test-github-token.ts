/**
 * Test script for GitHub token validation
 * 
 * Usage:
 *   npm run test:github-token -- <your-github-token>
 * 
 * Or set GITHUB_TOKEN environment variable:
 *   GITHUB_TOKEN=ghp_xxx... npm run test:github-token
 */

import { validateGitHubToken, checkTokenScopes } from '@libs/integrations/github';

async function main() {
    // Get token from command line arg or environment variable
    const token = process.argv[2] || process.env.GITHUB_TOKEN;

    if (!token) {
        console.error('❌ Error: No GitHub token provided');
        console.error('');
        console.error('Usage:');
        console.error('  npm run test:github-token -- <your-github-token>');
        console.error('  or');
        console.error('  GITHUB_TOKEN=ghp_xxx... npm run test:github-token');
        process.exit(1);
    }

    console.log('🔍 Validating GitHub token...\n');

    // Test basic validation
    const result = await validateGitHubToken(token);

    if (result.valid) {
        console.log('✅ Token is VALID');
        console.log(`   Username: ${result.username}`);

        if (result.scopes && result.scopes.length > 0) {
            console.log(`   Scopes: ${result.scopes.join(', ')}`);
        } else {
            console.log('   Scopes: (none or unable to determine)');
        }

        // Test scope checking for common PR-related permissions
        console.log('\n📋 Checking required scopes for PR operations...');
        const scopeCheck = await checkTokenScopes(token, ['repo']);

        if (scopeCheck.hasRequiredScopes) {
            console.log('✅ Token has required scopes for PR operations');
        } else {
            console.log(`⚠️  Missing required scopes: ${scopeCheck.missingScopes?.join(', ')}`);
            console.log('   Note: Some operations may not work without these permissions');
        }
    } else {
        console.log('❌ Token is INVALID');
        console.log(`   Error: ${result.error}`);
        process.exit(1);
    }

    console.log('\n✨ Validation complete!');
}

main().catch((error) => {
    console.error('❌ Unexpected error:', error.message);
    process.exit(1);
});
