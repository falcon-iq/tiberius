// libs/integrations/github/src/lib/prs.ts

import { Octokit } from 'octokit';
import { throttling } from '@octokit/plugin-throttling';
import { retry } from '@octokit/plugin-retry';
import { toCsv } from '@libs/shared/utils';
import type {
    IsoDate,
    GitHubPrPipelineConfig,
    PrStorage,
    DownloadAuthoredResult,
    SearchIssuesItem,
    PrMetaRow,
    CommentRow,
    FileRow,
    IndexRow,
    FailedRow,
} from './types';

export type {
    IsoDate,
    GitHubPrPipelineConfig,
    PrStorage,
    DownloadAuthoredResult,
    SearchIssuesItem,
    PrMetaRow,
    CommentRow,
    FileRow,
    IndexRow,
    FailedRow,
};

/* ------------------------------- Validation ------------------------------ */

const validateIsoDate = (s: string): IsoDate => {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) {
        throw new Error(`Invalid date '${s}'. Expected YYYY-MM-DD.`);
    }
    const d = new Date(`${s}T00:00:00Z`);
    if (Number.isNaN(d.getTime())) throw new Error(`Invalid date '${s}'.`);
    return s;
};

const defaultLog = (msg: string): void => {
    console.log(msg);
};

const noOpLog = (): void => {
    // no-op: silent by default for web builds
};

/* ------------------------------ Octokit setup ---------------------------- */

const MyOctokit = Octokit.plugin(throttling, retry);

const createOctokit = (token: string, log: (msg: string) => void): InstanceType<typeof MyOctokit> => {
    return new MyOctokit({
        auth: token,
        throttle: {
            onRateLimit: (
                retryAfter: number,
                options: { method?: string; url?: string } & Record<string, unknown>
            ) => {
                log(`GitHub rate limit hit for ${options.method ?? 'UNKNOWN'} ${options.url ?? 'UNKNOWN'}. retryAfter=${retryAfter}s`);
                // Returning true tells the plugin to retry after retryAfter seconds.
                return true;
            },
            onSecondaryRateLimit: (
                retryAfter: number,
                options: { method?: string; url?: string } & Record<string, unknown>
            ) => {
                log(`GitHub secondary rate limit for ${options.method ?? 'UNKNOWN'} ${options.url ?? 'UNKNOWN'}. retryAfter=${retryAfter}s`);
                return true;
            },
        },
        retry: {
            doNotRetry: ['429'], // throttling plugin handles these
        },
    });
};

/* ---------------------------- Key conventions ---------------------------- */

const prPrefix = (owner: string, repo: string, prNumber: number): string => {
    return `${owner}/${repo}/pr_${prNumber}`;
};

const runPrefix = (org: string, author: string, startDate: string, endDate: string): string => {
    return `${org}/author_${author}_${startDate}_to_${endDate}`;
};

const parseOwnerRepoFromSearchItem = (item: SearchIssuesItem): { owner: string; repo: string } => {
    const repoUrl = item.repository_url;
    if (!repoUrl) throw new Error('Missing repository_url on search item');

    const marker = '/repos/';
    const idx = repoUrl.indexOf(marker);
    if (idx === -1) throw new Error(`Unexpected repository_url format: ${repoUrl}`);

    const ownerRepo = repoUrl.slice(idx + marker.length); // OWNER/REPO
    const [owner, ...rest] = ownerRepo.split('/');
    const repo = rest.join('/');
    if (!owner || !repo) throw new Error(`Could not parse owner/repo from repository_url: ${repoUrl}`);

    return { owner, repo };
};

/* --------------------------- GitHub operations --------------------------- */

const searchAuthoredPRs = async (args: {
    octokit: InstanceType<typeof MyOctokit>;
    org: string;
    author: string;
    startDate: IsoDate;
    endDate: IsoDate;
    perPage: number;
    log: (msg: string) => void;
    hardCap?: number;
}): Promise<SearchIssuesItem[]> => {
    const q = `org:${args.org} is:pr author:${args.author} created:${args.startDate}..${args.endDate}`;

    // Octokit supports pagination via octokit.paginate for list-like endpoints.
    const items = await args.octokit.paginate(args.octokit.rest.search.issuesAndPullRequests, {
        q,
        per_page: args.perPage,
    });

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const mapped = items.map((it: any) => ({
        number: it.number,
        title: it.title,
        state: it.state,
        created_at: it.created_at,
        updated_at: it.updated_at,
        html_url: it.html_url,
        repository_url: it.repository_url,
    })) as SearchIssuesItem[];

    if (args.hardCap && mapped.length >= args.hardCap) {
        // Practical safeguard: GitHub search has well-known result limits; shard by date windows if you hit this.
        throw new Error(
            `Search returned ${mapped.length} results, which is at/above hard cap ${args.hardCap}. Shard the date range to avoid GitHub Search caps.`,
        );
    }

    return mapped;
};

const extractPrFull = async (args: {
    octokit: InstanceType<typeof MyOctokit>;
    storage: PrStorage;
    owner: string;
    repo: string;
    prNumber: number;
    perPage: number;
}): Promise<void> => {
    const { octokit, storage, owner, repo, prNumber, perPage } = args;

    const pr = await octokit.rest.pulls.get({ owner, repo, pull_number: prNumber });

    const prMeta: PrMetaRow = {
        owner,
        repo,
        pr_number: prNumber,
        pr_title: pr.data.title,
        pr_body: pr.data.body ?? null,
        pr_state: pr.data.state,
        pr_draft: pr.data.draft,
        pr_author: pr.data.user?.login,
        pr_created_at: pr.data.created_at,
        pr_updated_at: pr.data.updated_at,
        pr_merged_at: pr.data.merged_at ?? null,
        pr_mergeable_state: pr.data.mergeable_state,
        pr_additions: pr.data.additions,
        pr_deletions: pr.data.deletions,
        pr_changed_files: pr.data.changed_files,
        pr_commits_count: pr.data.commits,
        pr_issue_comments_count: pr.data.comments,
        pr_review_comments_count: pr.data.review_comments,
        pr_html_url: pr.data.html_url,
    };

    const metaKey = `${prPrefix(owner, repo, prNumber)}/pr_${prNumber}_meta.csv`;
    await storage.writeText(
        metaKey,
        toCsv([prMeta], [
            'owner',
            'repo',
            'pr_number',
            'pr_title',
            'pr_body',
            'pr_state',
            'pr_draft',
            'pr_author',
            'pr_created_at',
            'pr_updated_at',
            'pr_merged_at',
            'pr_mergeable_state',
            'pr_additions',
            'pr_deletions',
            'pr_changed_files',
            'pr_commits_count',
            'pr_issue_comments_count',
            'pr_review_comments_count',
            'pr_html_url',
        ]),
    );

    const issueComments = await octokit.paginate(octokit.rest.issues.listComments, {
        owner,
        repo,
        issue_number: prNumber,
        per_page: perPage,
    });

    const reviewInlineComments = await octokit.paginate(octokit.rest.pulls.listReviewComments, {
        owner,
        repo,
        pull_number: prNumber,
        per_page: perPage,
    });

    const reviews = await octokit.paginate(octokit.rest.pulls.listReviews, {
        owner,
        repo,
        pull_number: prNumber,
        per_page: perPage,
    });

    const prFiles = await octokit.paginate(octokit.rest.pulls.listFiles, {
        owner,
        repo,
        pull_number: prNumber,
        per_page: perPage,
    });

    const commentRows: CommentRow[] = [];

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    for (const c of issueComments as any[]) {
        commentRows.push({
            owner,
            repo,
            pr_number: prNumber,
            comment_type: 'ISSUE_COMMENT',
            comment_id: c.id,
            user: c.user?.login,
            created_at: c.created_at,
            body: c.body ?? null,
            state: null,
            is_reviewer: false,
            path: null,
            line: null,
            side: null,
        });
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    for (const c of reviewInlineComments as any[]) {
        commentRows.push({
            owner,
            repo,
            pr_number: prNumber,
            comment_type: 'REVIEW_INLINE_COMMENT',
            comment_id: c.id,
            user: c.user?.login,
            created_at: c.created_at,
            body: c.body ?? null,
            state: null,
            is_reviewer: true,
            path: c.path ?? null,
            line: c.line ?? null,
            side: c.side ?? null,
        });
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    for (const r of reviews as any[]) {
        commentRows.push({
            owner,
            repo,
            pr_number: prNumber,
            comment_type: 'REVIEW_SUMMARY',
            comment_id: r.id,
            user: r.user?.login,
            created_at: r.submitted_at,
            body: r.body ?? null,
            state: r.state ?? null,
            is_reviewer: true,
            path: null,
            line: null,
            side: null,
        });
    }

    const commentsKey = `${prPrefix(owner, repo, prNumber)}/pr_${prNumber}_comments.csv`;
    await storage.writeText(
        commentsKey,
        toCsv(commentRows, [
            'owner',
            'repo',
            'pr_number',
            'comment_type',
            'comment_id',
            'user',
            'created_at',
            'body',
            'state',
            'is_reviewer',
            'path',
            'line',
            'side',
        ]),
    );

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const fileRows: FileRow[] = (prFiles as any[]).map((f) => ({
        owner,
        repo,
        pr_number: prNumber,
        filename: f.filename,
        status: f.status,
        additions: f.additions,
        deletions: f.deletions,
        changes: f.changes,
        blob_url: f.blob_url,
        raw_url: f.raw_url,
        patch: f.patch,
    }));

    const filesKey = `${prPrefix(owner, repo, prNumber)}/pr_${prNumber}_files.csv`;
    await storage.writeText(
        filesKey,
        toCsv(fileRows, [
            'owner',
            'repo',
            'pr_number',
            'filename',
            'status',
            'additions',
            'deletions',
            'changes',
            'blob_url',
            'raw_url',
            'patch',
        ]),
    );
};

/* ------------------------------ Public API ------------------------------- */

export const downloadAuthoredPullRequests = async (
    token: string,
    cfg: GitHubPrPipelineConfig,
    storage: PrStorage
): Promise<DownloadAuthoredResult> => {
    // Validate token immediately
    if (!token || token.trim().length === 0) {
        throw new Error('GitHub token is required and cannot be empty');
    }

    const startDate = validateIsoDate(cfg.start_date);
    const endDate = validateIsoDate(cfg.end_date_authored);

    // Determine logging strategy
    const log = cfg.options?.log
        ?? (cfg.options?.enableDefaultLogging ? defaultLog : noOpLog);

    const octokit = createOctokit(token, log);

    if (storage.init) await storage.init();

    const authorSuffix = cfg.options?.authorSuffix ?? '_LinkedIn';
    const author = `${cfg.user}${authorSuffix}`;
    const perPage = cfg.options?.perPage ?? 100;

    const items = await searchAuthoredPRs({
        octokit,
        org: cfg.org,
        author,
        startDate,
        endDate,
        perPage,
        log,
        hardCap: cfg.options?.searchResultHardCap,
    });

    log(`Found ${items.length} PRs for author '${author}' in org '${cfg.org}' from ${startDate} to ${endDate}`);

    const runKeyPrefix = runPrefix(cfg.org, author, startDate, endDate);

    const indexRows: IndexRow[] = items.map((it) => {
        const { owner, repo } = parseOwnerRepoFromSearchItem(it);
        return {
            org: cfg.org,
            owner,
            repo,
            author,
            pr_number: it.number,
            title: it.title,
            state: it.state,
            created_at: it.created_at,
            updated_at: it.updated_at,
            html_url: it.html_url,
        };
    });

    // Sort similarly to the Python implementation
    indexRows.sort((a, b) => {
        const ca = a.created_at ?? '';
        const cb = b.created_at ?? '';
        if (ca !== cb) return ca.localeCompare(cb);
        if (a.owner !== b.owner) return a.owner.localeCompare(b.owner);
        if (a.repo !== b.repo) return a.repo.localeCompare(b.repo);
        return Number(a.pr_number ?? 0) - Number(b.pr_number ?? 0);
    });

    const failures: FailedRow[] = [];
    let downloaded = 0;

    for (let i = 0; i < items.length; i += 1) {
        const item = items[i];
        if (!item) continue;
        const prNumber = Number(item.number);
        const { owner, repo } = parseOwnerRepoFromSearchItem(item);

        try {
            log(`(${i + 1}/${items.length}) ${owner}/${repo} #${prNumber}`);
            await extractPrFull({ octokit, storage, owner, repo, prNumber, perPage });
            downloaded += 1;
        } catch (e) {
            failures.push({
                owner,
                repo,
                pr_number: prNumber,
                error: (e as Error).message ?? String(e),
                html_url: item.html_url,
            });
        }
    }

    // Write run-level artifacts
    await storage.writeText(
        `${runKeyPrefix}/prs_index.csv`,
        toCsv(indexRows, ['org', 'owner', 'repo', 'author', 'pr_number', 'title', 'state', 'created_at', 'updated_at', 'html_url']),
    );

    if (failures.length > 0) {
        await storage.writeText(
            `${runKeyPrefix}/prs_failed.csv`,
            toCsv(failures, ['owner', 'repo', 'pr_number', 'error', 'html_url']),
        );
    }

    await storage.writeText(`${runKeyPrefix}/_SUCCESS`, `authored ok: ${downloaded} failed: ${failures.length}\n`);

    return {
        runPrefix: runKeyPrefix,
        found: items.length,
        downloaded,
        failed: failures.length,
        failures,
    };
};
