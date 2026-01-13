import { downloadAuthoredPullRequests, FsPrStorage } from '@libs/integrations/github';
import type { GitHubPrPipelineConfig } from '@libs/integrations/github';


// class MemoryPrStorage implements PrStorage {
//     public files = new Map<string, string>();
//     async writeText(key: string, contents: string): Promise<void> {
//         this.files.set(key, contents);
//     }
// }

async function main() {
    const token = process.env.GH_PAT ?? ''; // for the test script only
    if (!token) throw new Error('Set GH_PAT in your shell for this test.');

    const cfg: GitHubPrPipelineConfig = {
        org: 'linkedin-multiproduct',
        user: 'bsteyn', // e.g. 'barry' or prefix used by your scheme
        start_date: '2025-01-01',
        end_date_authored: '2025-12-31',
        options: {
            authorSuffix: '_LinkedIn', // set to '_LinkedIn' if that’s your actual login suffix
            perPage: 100,
            enableDefaultLogging: true,
            // searchResultHardCap: 950,
        },
    };

    // const storage = new MemoryPrStorage();
    const storage = new FsPrStorage('/tmp/github_pr_dump'); // or wherever
    const result = await downloadAuthoredPullRequests(token, cfg, storage);

    console.log('Result:', result);
    // console.log('Files written:', storage.files.size);
    // console.log('Sample keys:', Array.from(storage.files.keys()).slice(0, 10));

    // // Optional: peek at index CSV
    // const indexKey = `${result.runPrefix}/prs_index.csv`;
    // console.log('Index CSV (first 500 chars):');
    // console.log((storage.files.get(indexKey) ?? '').slice(0, 500));
}

main().catch((e) => {
    console.error(e);
    process.exit(1);
});
