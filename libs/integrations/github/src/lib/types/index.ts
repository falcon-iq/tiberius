// libs/integrations/github/src/lib/types/index.ts

export type IsoDate = string;

export interface GitHubPrPipelineConfig {
    base_dir?: string; // optional: used by fs storage adapter, not required by core
    org: string;
    user: string;

    start_date: IsoDate;
    end_date_authored: IsoDate;

    options?: {
        perPage?: number; // default 100
        log?: (msg: string) => void;

        /**
         * Suffix to append to author name when searching GitHub.
         * Default: '_LinkedIn'
         */
        authorSuffix?: string;

        /**
         * Suffix to append to reviewer name when searching GitHub.
         * Default: '' (empty string)
         */
        reviewerSuffix?: string;

        /**
         * Safety valve for GitHub Search API's practical cap (~1000 results/query).
         * If you set this, core will throw if it finds >= cap, prompting you to shard by date range.
         */
        searchResultHardCap?: number; // e.g. 950

        /**
         * Enable default console.log logging.
         * Default: false (no logging unless custom logger provided)
         */
        enableDefaultLogging?: boolean;
    };
}

/**
 * Storage abstraction.
 * - Works in Electron (filesystem) and web (memory / upload).
 * - Keys are logical paths, e.g. "OWNER/REPO/pr_123/pr_123_meta.csv"
 */
export interface PrStorage {
    writeText(key: string, contents: string): Promise<void>;
    writeBinary?(key: string, contents: Uint8Array, contentType?: string): Promise<void>;

    /**
     * Optional. If present, core will call it once at start.
     * Useful for "mkdirp base dir" in fs storage, or no-op in web storage.
     */
    init?(): Promise<void>;
}

export interface DownloadAuthoredResult {
    runPrefix: string;
    found: number;
    downloaded: number;
    failed: number;
    failures: FailedRow[];
}

export type SearchIssuesItem = {
    number: number;
    title?: string;
    state?: string;
    created_at?: string;
    updated_at?: string;
    html_url?: string;
    repository_url?: string;
};

export type PrMetaRow = {
    owner: string;
    repo: string;
    pr_number: number;
    pr_title?: string;
    pr_body?: string | null;
    pr_state?: string;
    pr_draft?: boolean;
    pr_author?: string;
    pr_created_at?: string;
    pr_updated_at?: string;
    pr_merged_at?: string | null;
    pr_mergeable_state?: string;
    pr_additions?: number;
    pr_deletions?: number;
    pr_changed_files?: number;
    pr_commits_count?: number;
    pr_issue_comments_count?: number;
    pr_review_comments_count?: number;
    pr_html_url?: string;
};

export type CommentRow = {
    owner: string;
    repo: string;
    pr_number: number;
    comment_type: 'ISSUE_COMMENT' | 'REVIEW_INLINE_COMMENT' | 'REVIEW_SUMMARY';
    comment_id?: number;
    user?: string;
    created_at?: string;
    body?: string | null;
    state?: string | null;
    is_reviewer: boolean;
    path?: string | null;
    line?: number | null;
    side?: string | null;
};

export type FileRow = {
    owner: string;
    repo: string;
    pr_number: number;
    filename?: string;
    status?: string;
    additions?: number;
    deletions?: number;
    changes?: number;
    blob_url?: string;
    raw_url?: string;
    patch?: string;
};

export type IndexRow = {
    org: string;
    owner: string;
    repo: string;
    author: string;
    pr_number?: number;
    title?: string;
    state?: string;
    created_at?: string;
    updated_at?: string;
    html_url?: string;
};

export type FailedRow = {
    owner: string;
    repo: string;
    pr_number: number;
    error: string;
    html_url?: string;
};
