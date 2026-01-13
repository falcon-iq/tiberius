import { downloadReviewedPullRequests, FsPrStorage } from '@libs/integrations/github';
import type { GitHubPrPipelineConfig } from '@libs/integrations/github';

async function main() {
    const token = process.env.GH_PAT ?? ''; // for the test script only
    if (!token) throw new Error('Set GH_PAT in your shell for this test.');

    const cfg: GitHubPrPipelineConfig = {
        org: 'linkedin-multiproduct',
        user: 'bsteyn',
        start_date: '2025-01-01',
        end_date_authored: '2025-12-31', // reused by pipeline; rename later if you add end_date_reviewed
        options: {
            // IMPORTANT: reviewed-by expects a real GitHub login.
            // If your actual GitHub login is "bsteyn_LinkedIn", set reviewerSuffix to "_LinkedIn".
            // Otherwise leave it blank.
            reviewerSuffix: '_LinkedIn',
            perPage: 100,
            enableDefaultLogging: true,
            // searchResultHardCap: 950,
        },
    };

    const storage = new FsPrStorage('/tmp/github_pr_dump_reviewed');
    const result = await downloadReviewedPullRequests(token, cfg, storage);

    console.log('Result:', result);
}

main().catch((e) => {
    console.error(e);
    process.exit(1);
});
