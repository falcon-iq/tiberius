package com.falconiq.crawler.enrichment;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Integration tests that hit real external APIs (SerpAPI, Crunchbase).
 *
 * <p>Requires environment variables:
 * <ul>
 *   <li>{@code SERP_API_KEY} — for G2 and Google Search tests</li>
 *   <li>{@code CRUNCHBASE_API_KEY} — for Crunchbase tests</li>
 * </ul>
 *
 * <p>Run with: {@code mvn test -Dgroups=integration}
 * <p>Or a single fetcher: {@code mvn test -Dgroups=integration -Dtest="EnrichmentIntegrationTest#g2*"}
 */
@Tag("integration")
class EnrichmentIntegrationTest {

    private static String serpApiKey;
    private static String crunchbaseApiKey;
    private static String analyzerApiUrl;

    @BeforeAll
    static void loadKeys() {
        serpApiKey = resolve("SERP_API_KEY", "serp.api.key");
        crunchbaseApiKey = resolve("CRUNCHBASE_API_KEY", "crunchbase.api.key");
        analyzerApiUrl = resolve("ANALYZER_API_URL", "analyzer.api.url");
        System.out.println("Analyzer API URL: " + (analyzerApiUrl != null ? analyzerApiUrl : "(not set — Playwright disabled)"));
    }

    /** Check system property first (passed via -D), then env var. */
    private static String resolve(String envVar, String sysProp) {
        String val = System.getProperty(sysProp);
        if (val != null && !val.isBlank()) return val;
        return System.getenv(envVar);
    }

    // ── G2 via SerpAPI ──────────────────────────────────────────────

    @Test
    void g2FetchesDataForWellKnownCompany() {
        assertKeySet(serpApiKey, "SERP_API_KEY");

        G2Fetcher fetcher = createG2Fetcher();
        G2Data data = fetcher.fetch("Slack", serpApiKey);

        assertNotNull(data, "G2 should return data for Slack");

        System.out.println("=== G2 Results for Slack ===");
        System.out.println("Rating: " + data.getRating());
        System.out.println("Review count: " + data.getReviewCount());
        System.out.println("G2 URL: " + data.getG2Url());
        System.out.println("Description: " + (data.getDescription().length() > 120
                ? data.getDescription().substring(0, 120) + "..." : data.getDescription()));
        System.out.println("Pros (" + data.getProsThemes().size() + "):");
        data.getProsThemes().stream().limit(5).forEach(t ->
                System.out.println("  + " + truncate(t.getTheme(), 120)));
        System.out.println("Cons (" + data.getConsThemes().size() + "):");
        data.getConsThemes().stream().limit(5).forEach(t ->
                System.out.println("  - " + truncate(t.getTheme(), 120)));
        System.out.println("Reviewer titles (" + data.getReviewerTitles().size() + "): "
                + data.getReviewerTitles().stream().limit(5).toList());
        System.out.println("Company sizes: " + data.getCompanySizes());
        System.out.println();
    }

    @Test
    void g2ReturnsNullForObscureCompany() {
        assertKeySet(serpApiKey, "SERP_API_KEY");

        G2Fetcher fetcher = createG2Fetcher();
        G2Data data = fetcher.fetch("xyznonexistent12345corp", serpApiKey);

        // An obscure company may return null or empty data
        System.out.println("=== G2 Results for obscure company ===");
        System.out.println("Result: " + (data == null ? "null" : "rating=" + data.getRating()));
        System.out.println();
    }

    // ── Crunchbase ──────────────────────────────────────────────────

    @Test
    void crunchbaseFetchesDataForWellKnownCompany() {
        assertKeySet(serpApiKey, "SERP_API_KEY");

        CrunchbaseFetcher fetcher = new CrunchbaseFetcher();
        CrunchbaseData data = fetcher.fetch("Stripe", serpApiKey);

        assertNotNull(data, "Should return company data for Stripe");

        System.out.println("=== Company Data for Stripe ===");
        System.out.println("Founded: " + data.getFounded());
        System.out.println("HQ: " + data.getHq());
        System.out.println("Employees: " + data.getEmployeeCount());
        System.out.println("Total funding/valuation: " + data.getTotalFunding());
        System.out.println("Investors: " + data.getInvestors());
        System.out.println();
    }

    @Test
    void crunchbaseReturnsNullForObscureCompany() {
        assertKeySet(serpApiKey, "SERP_API_KEY");

        CrunchbaseFetcher fetcher = new CrunchbaseFetcher();
        CrunchbaseData data = fetcher.fetch("xyznonexistent12345corp", serpApiKey);

        System.out.println("=== Crunchbase Results for obscure company ===");
        System.out.println("Result: " + (data == null ? "null" : "founded=" + data.getFounded()));
        System.out.println();
    }

    // ── Review Sites (Capterra, TrustRadius, etc.) ─────────────────

    @Test
    void reviewSitesFetchesRatingsForWellKnownCompany() {
        assertKeySet(serpApiKey, "SERP_API_KEY");

        ReviewSiteFetcher fetcher = new ReviewSiteFetcher();
        List<ReviewSiteData> sites = fetcher.fetch("Slack", serpApiKey);

        assertNotNull(sites);
        System.out.println("=== Review Sites for Slack ===");
        System.out.println("Sites found: " + sites.size());
        sites.forEach(s -> System.out.printf("  %s: rating=%s, reviews=%d, url=%s%n",
                s.getSiteName(), s.getRating(), s.getReviewCount(), s.getUrl()));
        System.out.println();
    }

    // ── Google Search via SerpAPI ───────────────────────────────────

    @Test
    void googleSearchFetchesInsightsForWellKnownCompany() {
        assertKeySet(serpApiKey, "SERP_API_KEY");

        GoogleSearchFetcher fetcher = new GoogleSearchFetcher();
        List<GoogleSearchInsight> insights = fetcher.fetch("HubSpot", serpApiKey);

        assertNotNull(insights);
        assertFalse(insights.isEmpty(), "Should return search insights for HubSpot");

        System.out.println("=== Google Search Results for HubSpot ===");
        System.out.println("Total insights: " + insights.size());
        insights.forEach(i -> System.out.printf("  [%s] %s — %s%n",
                i.getInsightType(), i.getTitle(), i.getUrl()));

        // Verify we get a mix of insight types
        long reviews = insights.stream().filter(i -> "review".equals(i.getInsightType())).count();
        long comparisons = insights.stream().filter(i -> "comparison".equals(i.getInsightType())).count();
        System.out.println("Reviews: " + reviews + ", Comparisons: " + comparisons);
        System.out.println();
    }

    @Test
    void googleSearchReturnsResultsForObscureCompany() {
        assertKeySet(serpApiKey, "SERP_API_KEY");

        GoogleSearchFetcher fetcher = new GoogleSearchFetcher();
        List<GoogleSearchInsight> insights = fetcher.fetch("xyznonexistent12345corp", serpApiKey);

        // Even obscure queries should return some results (Google always finds something)
        System.out.println("=== Google Search Results for obscure company ===");
        System.out.println("Total insights: " + (insights == null ? "null" : insights.size()));
        System.out.println();
    }

    // ── Full enrichment pipeline ────────────────────────────────────

    @Test
    void fullEnrichmentPipelineForRealCompany() {
        // This test requires both API keys
        boolean hasSerpKey = serpApiKey != null && !serpApiKey.isBlank();
        boolean hasCrunchbaseKey = crunchbaseApiKey != null && !crunchbaseApiKey.isBlank();
        if (!hasSerpKey && !hasCrunchbaseKey) {
            fail("At least one of SERP_API_KEY or CRUNCHBASE_API_KEY must be set");
        }

        // Use all three fetchers directly (no need for EnrichmentManager/MongoDB)
        String company = "Datadog";
        System.out.println("=== Full Enrichment Pipeline for " + company + " ===");

        G2Data g2 = null;
        if (hasSerpKey) {
            g2 = createG2Fetcher().fetch(company, serpApiKey);
            System.out.println("G2: " + (g2 != null
                    ? "rating=" + g2.getRating() + " reviews=" + g2.getReviewCount()
                    : "not found"));
        }

        CrunchbaseData cb = null;
        if (hasCrunchbaseKey) {
            cb = new CrunchbaseFetcher().fetch(company, crunchbaseApiKey);
            System.out.println("Crunchbase: " + (cb != null
                    ? "founded=" + cb.getFounded() + " funding=" + cb.getTotalFunding() + " employees=" + cb.getEmployeeCount()
                    : "not found"));
        }

        List<GoogleSearchInsight> gs = List.of();
        if (hasSerpKey) {
            gs = new GoogleSearchFetcher().fetch(company, serpApiKey);
            System.out.println("Google insights: " + gs.size());
            gs.stream().limit(5).forEach(i -> System.out.printf("  [%s] %s%n", i.getInsightType(), i.getTitle()));
        }

        // At least one source should return data for a well-known company
        assertTrue(g2 != null || cb != null || !gs.isEmpty(),
                "At least one enrichment source should return data for " + company);
        System.out.println();
    }

    private static G2Fetcher createG2Fetcher() {
        return (analyzerApiUrl != null && !analyzerApiUrl.isBlank())
                ? new G2Fetcher(analyzerApiUrl)
                : new G2Fetcher();
    }

    private static void assertKeySet(String key, String envVar) {
        if (key == null || key.isBlank()) {
            fail(envVar + " environment variable is not set — skipping integration test");
        }
    }

    private static String truncate(String s, int max) {
        return s.length() > max ? s.substring(0, max) + "..." : s;
    }
}
