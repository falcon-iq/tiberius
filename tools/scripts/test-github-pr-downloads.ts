import { downloadAuthoredPullRequests, downloadReviewedPullRequests, FsPrStorage } from '@libs/integrations/github';
import type { GitHubPrPipelineConfig } from '@libs/integrations/github';

async function main() {
    const token = process.env.GH_PAT ?? ''; // for the test script only
    if (!token) throw new Error('Set GH_PAT in your shell for this test.');

    const cfg: GitHubPrPipelineConfig = {
        org: 'linkedin-multiproduct',
        user: 'anazeer', // e.g. 'barry' or prefix used by your scheme
        start_date: '2025-07-01',
        end_date: '2025-12-30',
        options: {
            authorSuffix: '_LinkedIn', // set to '_LinkedIn' if that's your actual login suffix
            perPage: 100,
            logLevel: 'debug', // 'debug' for verbose, 'error' for errors only, 'silent' to suppress all logs
            // searchResultHardCap: 950,
        },
    };

    // const storage = new MemoryPrStorage();
    const storage = new FsPrStorage('/tmp/github'); // or wherever
    let result = await downloadAuthoredPullRequests(token, cfg, storage);
    console.log('Pr Download Result:', result);

    result = await downloadReviewedPullRequests(token, cfg, storage);
    console.log('Pr Download Result:', result);
}

main().catch((e) => {
    console.error(e);
    process.exit(1);
});
