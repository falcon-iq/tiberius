# Benchmark Report Architecture

## Overview

The benchmark report feature lets a user compare their company's online presence against competitors using LLM-powered analysis. The pipeline spans four services: **MarketPilot Web App** (React) → **REST API** (Java) → **Crawler** (Java) → **Analyzer** (Python).

## User Flow

```
User fills form on /plan → REST API creates job → Crawler fetches pages → Analyzer runs LLM pipeline → Report generated → Email sent
```

## Step-by-Step

### 1. Form Submission (Web App)

**Route:** `/plan` — `BenchmarkForm` component

User provides:
- Email, company name, company URL
- 1–10 competitor URLs (can be AI-suggested via OpenAI)

On submit → `POST /api/company-benchmark-report/start`

### 2. Job Creation (REST API — Java)

**File:** `CompanyBenchmarkReportResource.java`

1. Normalizes & deduplicates URLs
2. Checks MongoDB for a cached report (TTL: 1 day) — returns immediately on cache hit
3. Creates/reuses `WebsiteCrawlDetail` docs for each URL
4. Creates `CompanyBenchmarkReport` doc (status: `NOT_STARTED`)
5. Fires HTTP POST to Crawler with the report ID
6. Returns report ID to frontend for polling

### 3. Crawling (Crawler — Java)

**File:** `CompanyBenchmarkReportResource.java` (crawler app)

1. Updates status → `CRAWL_IN_PROGRESS`
2. Crawls main company URL, then each competitor sequentially (max 100 pages each)
3. Reuses recently completed crawls for the same domain (dedup)
4. Stores HTML pages in S3 (or local FS)
5. Updates status → `CRAWL_COMPLETED`
6. Fires HTTP POST to Analyzer with the report ID

### 4. Analysis & Benchmark (Analyzer — Python/FastAPI)

**Endpoint:** `POST /company-benchmark`
**File:** `routers/company_benchmark.py`

Runs as an async background task:

#### Phase A: Per-Website Analysis (already done during crawl)
Each website goes through the 6-step pipeline:
1. Load pages from storage
2. Clean HTML → plain text
3. Classify pages (LLM) — product, blog, pricing, etc.
4. Extract offerings (LLM) — products/services with features
5. Synthesize top 5 offerings (LLM)
6. Generate per-company report

#### Phase B: Multi-Company Benchmark
1. **Wait for all analyses** to complete (30-min timeout, polls MongoDB)
2. **Build company overviews** — logo (Google Favicons), tagline (Wikidata), top offerings
3. **Generate comparison prompts** (LLM) — N prompts across categories:
   - Types: comparison, recommendation, feature inquiry, best-for-use-case
   - Deduplicates across batches using angle taxonomy
4. **Evaluate each prompt** (LLM) — extracts per-company mentions with:
   - Sentiment score (-1.0 to 1.0)
   - Strengths/weaknesses mentioned
   - Winner determination
5. **Summarize results** — win counts, avg sentiment, top strengths/weaknesses, key insights
6. **Normalize product categories** — cross-company comparison table
7. **Generate reports:**
   - `benchmark-{id}.json` — full structured result
   - `benchmark-{id}.md` — markdown report
   - `benchmark-{id}.html` — styled HTML for web/email
8. **Update MongoDB** — status → `COMPLETED`, set `reportUrl` + `htmlReportUrl`
9. **Send email notification** via AWS SES (non-blocking, failure doesn't fail the job)

### 5. Frontend Polling & Display

**Component:** `BenchmarkProgress`

Polls `GET /api/company-benchmark-report/{id}` every 4 seconds via TanStack Query.

```
NOT_STARTED (5%) → CRAWL_IN_PROGRESS (20%) → CRAWL_COMPLETED (40%)
→ ANALYSIS_IN_PROGRESS (55%) → ANALYSIS_COMPLETED (70%)
→ BENCHMARK_REPORT_IN_PROGRESS (85%) → COMPLETED (100%)
```

On completion: "View Report" button links to HTML report via CDN (`cdn.trymarketpilot.com/analyzer/...`) or analyzer endpoint fallback.

## Service Communication

```
[Browser]
  │ POST /api/company-benchmark-report/start
  ▼
[REST API :8080] ──MongoDB──> CompanyBenchmarkReport doc
  │ POST /api/company-benchmark-report/process
  ▼
[Crawler :8080]  ──S3──> crawled HTML pages
  │ POST /company-benchmark
  ▼
[Analyzer :8000] ──S3──> reports (JSON/MD/HTML)
  │                ──MongoDB──> status updates
  │                ──SES──> email notification
  ▼
[User gets email + views report on CDN]
```

**In AWS:** Crawler discovered via Cloud Map DNS (`crawler.falcon-iq.local:8080`). Analyzer behind public ALB. Shared S3 bucket for all storage.

## Key Data Models

### CompanyBenchmarkReport (MongoDB)

| Field | Purpose |
|---|---|
| `userId` | Email for notifications |
| `companyName` | Display name |
| `companyCrawlDetailId` | Ref to main company crawl |
| `competitionCrawlDetailIds` | Refs to competitor crawls |
| `companyLinkNormalized` | Cache key (normalized URL) |
| `competitorLinksNormalized` | Cache key (sorted, comma-joined) |
| `reportUrl` | S3 key → JSON result |
| `htmlReportUrl` | S3 key → HTML report |
| `status` | Pipeline status enum |

### MultiCompanyBenchmarkResult (Analyzer output)

```
├── main_company: str
├── competitors: [str]
├── company_overviews: {name → CompanyOverview}
│     ├── logo_url, tagline, categories
│     └── top_offerings: [{product_name, category, description, key_features}]
├── prompts: [GeneratedPrompt]
├── evaluations: [MultiCompanyPromptEvaluation]
│     ├── prompt_text, category, llm_response
│     ├── company_mentions: {name → {sentiment, strengths, weaknesses, recommended}}
│     └── winner: str
├── summary: MultiCompanyBenchmarkSummary
│     ├── company_stats: [{wins, avg_sentiment, top_strengths, top_weaknesses}]
│     └── key_insights: [str]
└── product_comparison_groups: [{group_name, entries}]
```

## Key Optimizations

- **Crawl caching** — reuses recent crawls for same domain
- **Report caching** — returns cached reports within TTL (1 day)
- **Async processing** — all heavy work runs as background tasks (202 responses)
- **Parallel Wikidata fetching** — taglines fetched concurrently
- **Non-blocking email** — SES failure doesn't fail the benchmark
