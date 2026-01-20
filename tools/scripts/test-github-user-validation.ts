#!/usr/bin/env tsx
/**
 * Test script for GitHub user validation
 * 
 * Usage:
 *   GITHUB_TOKEN=ghp_xxx... npx tsx tools/scripts/test-github-user-validation.ts
 */

import { validateGitHubUser } from '@libs/integrations/github';

async function main() {
    const token = process.env.GITHUB_TOKEN;

    if (!token) {
        console.error('❌ Error: GITHUB_TOKEN environment variable is required');
        console.error('Usage: GITHUB_TOKEN=ghp_xxx... npx tsx tools/scripts/test-github-user-validation.ts');
        process.exit(1);
    }

    // Test cases
    const testUsers = [
        'anazeer_Linkedin',
        'torvalds',          // Linus Torvalds
        'invalid-user-xyz-123-does-not-exist',  // Should not exist
    ];

    console.log('🔍 Testing GitHub User Validation\n');
    console.log('='.repeat(60));

    for (const username of testUsers) {
        console.log(`\n📝 Testing user: "${username}"`);
        console.log('-'.repeat(60));

        const result = await validateGitHubUser(token, username);

        if (result.valid) {
            console.log('✅ User found!');
            console.log(`   Username: ${result.user?.login}`);
            console.log(`   Name: ${result.user?.name || '(not set)'}`);
            console.log(`   Email: ${result.user?.email || '(not public)'}`);
            console.log(`   Type: ${result.user?.type}`);
            console.log(`   ID: ${result.user?.id}`);
            console.log(`   Avatar: ${result.user?.avatar_url}`);
        } else {
            console.log('❌ User not found');
            console.log(`   Error: ${result.error}`);
        }
    }

    console.log('\n' + '='.repeat(60));
    console.log('✨ Test complete!');
}

main().catch((error) => {
    console.error('❌ Fatal error:', error);
    process.exit(1);
});
