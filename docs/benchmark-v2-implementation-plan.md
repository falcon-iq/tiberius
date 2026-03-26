# Benchmark v2 — Full Implementation Plan

_Reference document for Claude Code. Covers Sprints 1–4 (no shadow rollout)._

---

## Sprint 1: Grounded Extraction (Analyzer — Python)

### Change 1: Enhance HTML cleaner to extract structured data
**File:** `apps/falcon-iq-analyzer/src/falcon_iq_analyzer/services/html_cleaner.py` (modify)

Currently extracts `title`, `meta_description`, and flattened `clean_text`. Add:
- **JSON-LD** blocks (`<script type="application/ld+json">`) — machine-readable product/org data, zero hallucination risk
- **Open Graph tags** (`og:title`, `og:description`, `og:type`, `og:image`)
- **HTML tables** — pricing grids, feature comparison tables (preserve structure, don't flatten)
- **Heading hierarchy** — H1/H2/H3 with their content as sections (preserves page structure instead of one blob)
- **Named links** from integration/partner pages (link text + href)

The `PageInfo` model gets new optional fields for this structured data.

### Change 2: Add new data models with evidence fields
**File:** `apps/falcon-iq-analyzer/src/falcon_iq_analyzer/models/domain.py` (modify)

- Add `Evidence` model: `{url: str, quote: str}` — a source snippet tied to a page URL
- Add `StructuredPageData` model for JSON-LD, OG tags, tables, headings
- Modify `Offering` to require `evidence: list[Evidence]` and `confidence: float`
- Modify `TopOffering`: remove `selling_script`, add `evidence_summary: str` and `evidence: list[Evidence]`
- Add `PricingPlan` model: `{name, price, currency, billing_period, evidence[]}`
- Add `Integration` model: `{name, type (native|api|partner), evidence[]}`
- Modify `AnalysisResult` to include `pricing_plans`, `integrations`, `verified_claims`

### Change 3: Rewrite extraction prompts with strict evidence contract
**File:** `apps/falcon-iq-analyzer/src/falcon_iq_analyzer/llm/prompts.py` (modify)

- **Replace `EXTRACT_SYSTEM`** (lines 25-38) — current prompt says "extract features mentioned" loosely. New prompt: strict extraction engine with "You MUST only use the provided SOURCES. If a field cannot be supported by a quoted snippet, output null. Never guess."
- **Replace `EXTRACT_USER`** (lines 40-44) — pass page content as `<SOURCES>` blocks with URL attribution, require `evidence[]` arrays in output
- **Replace `SYNTHESIZE_SYSTEM`** (lines 46-59) — remove `selling_script` generation. New prompt synthesizes across pages with confidence scoring (HIGH/MEDIUM only pass through)
- **Replace `SYNTHESIZE_USER`** (lines 61-65) — include source URL per extraction so evidence chains preserved

### Change 4: Two-pass extraction logic
**File:** `apps/falcon-iq-analyzer/src/falcon_iq_analyzer/services/extractor.py` (modify)

Currently 1 LLM call per page → takes whatever JSON comes back. Change to:
- **Pass 1 (verbatim):** Extract only what's explicitly stated. Each offering/feature/claim must include a `quote` from the page text.
- **Pass 2 (verification):** Separate LLM call receives candidate extractions + original page text, checks: does evidence support each claim? Verdict: `supported | not_supported | ambiguous`. Claims that fail → dropped.

### Change 5: Add deterministic structured extractor
**File:** `apps/falcon-iq-analyzer/src/falcon_iq_analyzer/services/structured_extractor.py` (new)

Non-LLM service that extracts data from DOM before LLM touches it:
- Parse JSON-LD for product/organization schema data
- Parse pricing tables into structured `PricingPlan` objects
- Parse integration pages (link text from `/integrations` pages)
- This data gets passed INTO the LLM extraction prompt as "pre-verified facts"

### Change 6: Add data validators
**File:** `apps/falcon-iq-analyzer/src/falcon_iq_analyzer/services/validators.py` (new)

Deterministic post-LLM validation:
- Pricing: currency must be ISO 4217, price must be numeric or null, billing period must be `monthly|annual|one_time|usage_based|contact_sales`
- Integrations: names must match on-page text exactly (cross-ref with structured extractor output)
- Offerings: must appear on at least one commercial page (not just blog)
- Dedup: no duplicate offerings by product name

### Change 7: Update synthesis with evidence chain
**File:** `apps/falcon-iq-analyzer/src/falcon_iq_analyzer/services/synthesizer.py` (modify)

- Remove `selling_script` from output
- Input text now includes source URLs per extraction
- Output requires `evidence_summary` (factual, backed by page quotes) instead of selling script
- Confidence scoring: only HIGH + MEDIUM confidence items pass through

### Change 8: Update analysis pipeline to use new components
**File:** `apps/falcon-iq-analyzer/src/falcon_iq_analyzer/pipeline/analyzer.py` (modify)

Current 6-step flow becomes ~8 steps:
1. Load pages (same)
2. Clean HTML + extract structured data (enhanced — Change 1)
3. Classify pages (same)
4. **Deterministic extraction** from structured data (new — Change 5)
5. **LLM extraction** with evidence contract (rewritten — Changes 3+4)
6. **Verification pass** — LLM checks extractions against source text (new — Change 4)
7. **Validation** — deterministic rules drop invalid data (new — Change 6)
8. Synthesize top offerings + generate report (modified — Change 7)

---

## Sprint 2: JS-Capable Crawling (Crawler — Java + new Python sidecar)

### Change 9: Add Playwright rendering service
**File:** `apps/falcon-iq-analyzer/src/falcon_iq_analyzer/services/renderer.py` (new)

Lightweight async service:
- Accepts a URL, launches Playwright (headless Chromium), renders page, returns full HTML
- Exposed as FastAPI endpoint: `POST /render` on the analyzer (already Python)
- Timeout + max page size limits

### Change 10: Add JS detection heuristic to crawler
**Files in:** `apps/falcon-iq-crawler/` (modify)

After JSoup fetches a page:
- If extracted text < 400 chars AND HTML is mostly `<script>` tags → mark for headless re-fetch
- Call Playwright renderer endpoint, get full HTML, re-store
- "Lane A / Lane B" pattern

### Change 11: Add priority queue + sitemap crawling
**Files in:** `apps/falcon-iq-crawler/` (modify)

- Fetch `robots.txt` and `sitemap.xml` first
- Seed priority queue with high-signal paths: `/pricing`, `/products`, `/features`, `/solutions`, `/integrations`, `/customers`, `/case-studies`, `/security`
- Category quotas: pricing ≤10, features ≤30, docs ≤200, blog ≤10
- URL canonicalization: collapse UTM params, trailing slashes, www vs non-www

### Change 12: Add `playwright` dependency
**File:** `apps/falcon-iq-analyzer/pyproject.toml` (modify)

Add `playwright` dependency + setup step for browser binaries.

---

## Sprint 3: External Enrichment (Analyzer — Python)

### Change 13: Add enrichment data models
**File:** `apps/falcon-iq-analyzer/src/falcon_iq_analyzer/models/enrichment.py` (new)

All enrichment types:
- `ExternalSource` enum (`g2`, `crunchbase`, `google_search`, `wikidata`)
- `ExternalFact` — single verifiable fact with source URL
- `ReviewTheme` — recurring theme from customer reviews with sample quotes
- `G2Data` — rating, review count, pros/cons themes, reviewer titles, company sizes
- `CrunchbaseData` — founded, HQ, employee count, funding, investors
- `GoogleSearchInsight` — search result classified as review/comparison/complaint
- `EnrichmentResult` — all external data for one company
- `VerifiedClaim` — a website claim with `verified|unverified|contradicted` status
- `EnrichedCompanyProfile` — complete enriched profile

### Change 14: Add enrichment service package
**Directory:** `apps/falcon-iq-analyzer/src/falcon_iq_analyzer/services/enrichment/` (new package)

- `__init__.py`
- `router.py` — orchestrator: decides which sources to fetch per company, runs in parallel via `asyncio.gather`, returns `EnrichmentResult`. Follows `wikidata_service.py` pattern (async httpx, graceful degradation).
- `g2.py` — G2 data fetcher. Uses SerpAPI to search `"site:g2.com {company}"`, parses structured snippets for rating, review count, pros/cons themes.
- `crunchbase.py` — Crunchbase API fetcher. Uses Basic API (free 200/day) for founded year, employee count, funding, investors. Falls back to scraping if no API key.
- `google_search.py` — SerpAPI integration. Runs targeted queries (`"{company} reviews"`, `"{company} pricing"`, `"{company} vs competitors"`), classifies results.
- `verifier.py` — LLM-powered cross-referencing. Takes website claims + external evidence, outputs `verified|unverified|contradicted` per claim.

### Change 15: Add enrichment settings
**File:** `apps/falcon-iq-analyzer/src/falcon_iq_analyzer/config.py` (modify)

New settings (env prefix `WEB_ANALYZER_`):
- `crunchbase_api_key: str = ""`
- `serp_api_key: str = ""`
- `enrichment_enabled: bool = True`

### Change 16: Wire enrichment into benchmark pipeline
**File:** `apps/falcon-iq-analyzer/src/falcon_iq_analyzer/pipeline/company_benchmark.py` (modify)

After Wikidata tagline fetch (line ~197), add:
1. Call `enrich_all_companies()` — parallel enrichment across all companies
2. Call `verify_claims()` — cross-ref website claims against external evidence
3. Attach enrichment data + verified claims to `CompanyOverview`

### Change 17: Extend CompanyOverview and benchmark result models
**File:** `apps/falcon-iq-analyzer/src/falcon_iq_analyzer/models/company_benchmark.py` (modify)

- Add `enrichment: Optional[EnrichmentResult]` and `verified_claims: list[VerifiedClaim]` to `CompanyOverview`
- Add `enriched_profiles: dict[str, EnrichedCompanyProfile]` to `MultiCompanyBenchmarkResult`

### Change 18: Add `ENRICHMENT_IN_PROGRESS` status
**File:** `apps/falcon-iq-rest/src/main/java/com/example/domain/objects/CompanyBenchmarkReport.java` (modify)

Add new enum value to status. Update frontend progress component to show this step (~62% progress).

---

## Sprint 4: Personas + Grounded Prompts + Evaluation

### Change 19: Add persona builder service
**File:** `apps/falcon-iq-analyzer/src/falcon_iq_analyzer/services/persona_builder.py` (new)

Builds buyer personas from **observable signals only**:

| Signal | Source | Inferred Persona |
|--------|--------|-----------------|
| Security/compliance pages (SOC 2, SSO, SAML) | Crawled pages | CTO / CISO buyer |
| Self-serve pricing ($29/mo) | Extraction | SMB segment |
| "Contact sales" + SSO | Extraction | Enterprise buyer |
| CRM integrations (Salesforce, HubSpot) | Extraction | RevOps buyer |
| Dev tools (GitHub, Jira) | Extraction | CTO/Engineering buyer |
| G2 reviewer titles | Enrichment | Actual buyer roles |
| Named customers/case studies | Extraction | Target industries |

Output: `list[CustomerPersona]` with evidence citations for each inference.

### Change 20: Add persona data models
**File:** `apps/falcon-iq-analyzer/src/falcon_iq_analyzer/models/enrichment.py` (extend)

- `CustomerPersona` — role, segment, company_size, industries, buying_triggers, top_concerns, evidence
- `BuyerRole` — title, level (C-suite/VP/Director/Manager), cares_about

### Change 21: Rewrite prompt generation with answerability tagging
**File:** `apps/falcon-iq-analyzer/src/falcon_iq_analyzer/llm/multi_benchmark_prompts.py` (modify)

Replace `MULTI_BENCHMARK_GENERATE_SYSTEM` and `MULTI_BENCHMARK_GENERATE_USER`:
- Prompts generated FROM personas, FOR verified facts
- Every prompt references a specific extracted fact or verified claim
- Each prompt gets `answerability` tag: `answerable_from_sources | needs_external_enrichment | unknown`
- **Hard guardrails:**
  - If integrations list empty → no integration questions
  - If pricing confidence < 0.6 → clarifying questions only, not comparisons
  - If no case studies → no "success story" questions

### Change 22: Update context blocks with evidence provenance
**File:** `apps/falcon-iq-analyzer/src/falcon_iq_analyzer/services/multi_benchmark_service.py` (modify)

`_build_context_block_for_companies()` currently passes synthesized offerings as website data. Change to:
- Tag each fact with source: `[from /pricing page]`, `[from G2 reviews]`, `[from Crunchbase]`
- Include external evidence alongside website data
- Separate verified vs unverified claims in context block

### Change 23: Fix eval system prompt
**File:** `apps/falcon-iq-analyzer/src/falcon_iq_analyzer/llm/prompts.py` (modify)

Replace `BENCHMARK_EVAL_SYSTEM = "You are a helpful assistant."` (line 121) with:
```
You are a knowledgeable business technology advisor. Answer honestly.
If you don't have reliable information about a specific product or feature,
say so rather than guessing. Do not make up pricing, feature claims, or customer counts.
```

### Change 24: Add fact-checked scoring to evaluation
**File:** `apps/falcon-iq-analyzer/src/falcon_iq_analyzer/services/multi_benchmark_service.py` (modify)

`evaluate_single_prompt_multi()` currently scores sentiment/winner. Add third step:
1. Send prompt to LLM (existing)
2. Analyze response for mentions (existing)
3. **Fact-check response** against verified company profile (new): Which facts did LLM get right? Wrong? Hallucinate? Miss?

New fields on `MultiCompanyPromptEvaluation`:
- `factual_accuracy: float` (0-1)
- `facts_confirmed: list[str]`
- `facts_wrong: list[str]`
- `facts_hallucinated: list[str]`
- `knowledge_gaps: list[str]`

### Change 25: Update report generation with evidence trail
**Files:** `services/multi_benchmark_service.py`, `services/html_report_generator.py` (modify)

- Every claim links to its source (page URL, G2, Crunchbase)
- Add "External Validation" section: G2 ratings, review themes, funding data
- Add "Fact-Check Scorecard": LLM accuracy per company
- Confidence indicators on claims
- Verified vs unverified claims shown separately

### Change 26: Add persona-based insights to report
**File:** `apps/falcon-iq-analyzer/src/falcon_iq_analyzer/services/multi_benchmark_service.py` (modify)

New report section: "For a CTO evaluating fleet management, Company A wins because..." — persona-specific insights from evaluation results.

---

## File Summary

### New Files (11)
| File | Sprint | Purpose |
|------|--------|---------|
| `services/structured_extractor.py` | 1 | Deterministic DOM extraction (JSON-LD, tables, OG tags) |
| `services/validators.py` | 1 | Post-LLM data validation rules |
| `services/renderer.py` | 2 | Playwright headless rendering service |
| `models/enrichment.py` | 3 | All enrichment + persona data models |
| `services/enrichment/__init__.py` | 3 | Package init |
| `services/enrichment/router.py` | 3 | Enrichment orchestrator |
| `services/enrichment/g2.py` | 3 | G2 review data fetcher |
| `services/enrichment/crunchbase.py` | 3 | Crunchbase company data fetcher |
| `services/enrichment/google_search.py` | 3 | Google Search insights via SerpAPI |
| `services/enrichment/verifier.py` | 3 | Cross-ref claims vs external evidence |
| `services/persona_builder.py` | 4 | Buyer persona construction from signals |

### Modified Files (11)
| File | Sprint | Changes |
|------|--------|---------|
| `services/html_cleaner.py` | 1 | Add JSON-LD, OG tags, table, heading extraction |
| `models/domain.py` | 1 | Add Evidence, StructuredPageData, PricingPlan, Integration models; modify Offering, TopOffering, AnalysisResult |
| `llm/prompts.py` | 1, 4 | Rewrite EXTRACT_SYSTEM/USER, SYNTHESIZE_SYSTEM/USER; fix BENCHMARK_EVAL_SYSTEM |
| `services/extractor.py` | 1 | Two-pass extraction with verification |
| `services/synthesizer.py` | 1 | Remove selling_script, add evidence chain + confidence |
| `pipeline/analyzer.py` | 1 | Add structured extraction, verification, validation steps |
| `config.py` | 3 | Add crunchbase_api_key, serp_api_key, enrichment_enabled |
| `models/company_benchmark.py` | 3, 4 | Extend CompanyOverview, MultiCompanyBenchmarkResult, MultiCompanyPromptEvaluation |
| `pipeline/company_benchmark.py` | 3 | Wire enrichment after tagline fetch |
| `llm/multi_benchmark_prompts.py` | 4 | Persona-driven prompt gen with answerability tagging |
| `services/multi_benchmark_service.py` | 4 | Evidence context blocks, fact-checked eval, persona insights |

### Other Changes
| File | Sprint | Changes |
|------|--------|---------|
| `apps/falcon-iq-crawler/` (multiple Java files) | 2 | Priority queue, JS detection, sitemap parsing |
| `apps/falcon-iq-analyzer/pyproject.toml` | 2 | Add playwright dependency |
| `CompanyBenchmarkReport.java` (REST API) | 3 | Add ENRICHMENT_IN_PROGRESS status |
| Frontend progress component | 3 | Add enrichment progress step |
| `services/html_report_generator.py` | 4 | Evidence trail, fact-check scorecard, persona insights |

---

## Core Design Rule

**No evidence → no claim.** Every output field is either:
1. Supported by at least one on-domain source snippet (URL + quote), OR
2. Supported by explicitly labeled third-party sources, OR
3. Returned as `null` / `unknown`

This single rule kills hallucinations by construction.
