# Enrichment Data Summary

All data fetched via **SerpAPI** (single API key). No Crunchbase or G2 API keys needed.

---

## 1. G2 Reviews (3 SerpAPI calls)

| Field | Example (Slack) | Source |
|-------|-----------------|--------|
| **Rating** | 4.5 / 5 | SerpAPI rich snippet `detected_extensions.rating` |
| **Review count** | 38,317 | SerpAPI rich snippet `detected_extensions.reviews` |
| **G2 URL** | https://www.g2.com/products/slack/reviews | SerpAPI organic result link |
| **Description** | "Users consistently praise Slack for its organized communication and seamless integrations..." | SerpAPI snippet (truncated ~160 chars by Google) |
| **Pros** (up to 10) | "Slack is very smooth and easy to use, especially when working with group channels." | SerpAPI search: `site:g2.com/products/{slug}/reviews "What do you like best"` — real G2 user review text |
| **Cons** (up to 10) | "Common complaints about Slack include overwhelming notification overload..." | SerpAPI search: `site:g2.com/products/{slug}/reviews "What do you dislike"` — real G2 user review text |
| Reviewer titles | _(not available via SerpAPI)_ | — |
| Company sizes | _(not available via SerpAPI)_ | — |

---

## 2. Company Data / Knowledge Graph (2 SerpAPI calls)

| Field | Example (Stripe) | Source |
|-------|-------------------|--------|
| **Founded** | 2010, San Francisco, CA | Google Knowledge Graph |
| **HQ** | Dublin, Ireland | Google Knowledge Graph |
| **Employees** | 8,500 (2025) | Google Knowledge Graph |
| **Valuation/Funding** | $159 billion | Google Knowledge Graph |
| **Investors** | _(extracted from snippets when present)_ | Google organic snippets — pattern matching "backed by X, Y" |

---

## 3. Review Sites (1 SerpAPI call)

Ratings from third-party review platforms, extracted from a single search.

| Site | Rating | Reviews | URL (Example: Slack) |
|------|--------|---------|----------------------|
| **Capterra** | 4.7 / 5 | 24,027 | https://www.capterra.com/p/135003/Slack/reviews/ |
| **TrustRadius** | 9.0 / 10 | 9,906 | https://www.trustradius.com/products/slack/reviews |
| **Trustpilot** | 2.4 / 5 | 345 | https://www.trustpilot.com/review/slack.com |
| **GetApp** | 4.7 / 5 | 24,025 | https://www.getapp.com/collaboration-software/a/slack/ |
| **PeerSpot** | _(when available)_ | — | — |
| **SoftwareAdvice** | _(when available)_ | — | — |

---

## 4. Google Search Insights (3 SerpAPI calls)

Targeted queries: `"{company}" reviews`, `"{company}" pricing`, `"{company}" vs competitors`.

| Classification | Example (HubSpot) | How classified |
|---------------|---------------------|----------------|
| **review** | "Read Customer Service Reviews of hubspot.com" (Trustpilot) | URL contains review site domain |
| **comparison** | "13 HubSpot Alternatives That Won't Break the Bank" | Text contains "vs", "alternative", "compared to" |
| **complaint** | _(when found)_ | Text contains "terrible", "problem", "issue", etc. |
| **general** | "HubSpot Review 2026: Is It Really The Best All-In-One CRM?" | Default |

Each insight includes: query, title, snippet, URL, insight_type.

---

## API Usage Per Company

| Source | SerpAPI Calls | Data |
|--------|--------------|------|
| G2 | 3 | Rating, reviews, pros, cons, description, URL |
| Company Data | 2 | Founded, HQ, employees, valuation, investors |
| Review Sites | 1 | Ratings from Capterra, TrustRadius, Trustpilot, GetApp |
| Google Search | 3 | 10-15 classified insights (reviews, comparisons, complaints) |
| **Total** | **9 per company** | |

With MongoDB TTL caching (G2: 7d, company data: 30d, Google: 3d), repeated enrichment for the same company hits cache instead of SerpAPI.

---

## How to Run Integration Tests

```bash
cd apps/falcon-iq-crawler

# All sources
mvn test -Pintegration

# Individual
mvn test -Pintegration -Dtest="EnrichmentIntegrationTest#g2*"
mvn test -Pintegration -Dtest="EnrichmentIntegrationTest#crunchbase*"
mvn test -Pintegration -Dtest="EnrichmentIntegrationTest#reviewSites*"
mvn test -Pintegration -Dtest="EnrichmentIntegrationTest#googleSearch*"
mvn test -Pintegration -Dtest="EnrichmentIntegrationTest#fullEnrichment*"
```

Requires `SERP_API_KEY` environment variable.
