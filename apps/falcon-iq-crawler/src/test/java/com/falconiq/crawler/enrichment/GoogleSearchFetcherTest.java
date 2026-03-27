package com.falconiq.crawler.enrichment;

import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.*;

class GoogleSearchFetcherTest {

    @Test
    void returnsEmptyListWhenNoApiKey() {
        GoogleSearchFetcher fetcher = new GoogleSearchFetcher(url -> { throw new AssertionError("Should not call HTTP"); });
        assertEquals(List.of(), fetcher.fetch("Acme", null));
        assertEquals(List.of(), fetcher.fetch("Acme", ""));
        assertEquals(List.of(), fetcher.fetch("Acme", "   "));
    }

    @Test
    void classifiesReviewSiteResults() {
        GoogleSearchFetcher fetcher = fakeGoogle(200, """
                {
                  "organic_results": [
                    {
                      "title": "Acme Reviews",
                      "snippet": "Acme is a great product...",
                      "link": "https://www.g2.com/products/acme/reviews"
                    },
                    {
                      "title": "Acme on Capterra",
                      "snippet": "Read reviews about Acme...",
                      "link": "https://www.capterra.com/p/12345/acme"
                    },
                    {
                      "title": "Acme Pricing",
                      "snippet": "Start at $10/month",
                      "link": "https://acme.com/pricing"
                    }
                  ]
                }
                """);

        List<GoogleSearchInsight> results = fetcher.fetch("Acme", "test-key");

        // 3 queries * 3 results each = 9 total
        assertEquals(9, results.size());

        // Check classification of first query's results
        assertEquals("review", results.get(0).getInsightType(), "g2.com → review");
        assertEquals("review", results.get(1).getInsightType(), "capterra.com → review");
        assertEquals("general", results.get(2).getInsightType(), "acme.com/pricing → general");
    }

    @Test
    void classifiesComparisonContent() {
        assertEquals("comparison", GoogleSearchFetcher.classifyResult(
                "Acme vs Competitor", "Which is Better?", "https://blog.example.com/acme-vs-competitor"));
    }

    @Test
    void classifiesVersusContent() {
        assertEquals("comparison", GoogleSearchFetcher.classifyResult(
                "Compare", "Acme versus Competitor features", "https://example.com/compare"));
    }

    @Test
    void classifiesAlternativeContent() {
        assertEquals("comparison", GoogleSearchFetcher.classifyResult(
                "Top Acme alternative tools", "Find the best alternatives", "https://example.com/alt"));
    }

    @Test
    void classifiesComplaintContent() {
        assertEquals("complaint", GoogleSearchFetcher.classifyResult(
                "Acme is terrible", "I had a terrible problem with support", "https://reddit.com/r/acme"));
    }

    @Test
    void classifiesComplaintByIssueKeyword() {
        assertEquals("complaint", GoogleSearchFetcher.classifyResult(
                "Acme", "Major issue with billing", "https://example.com/forum"));
    }

    @Test
    void reviewDomainTakesPriority() {
        // A trustpilot URL with "vs" in the title — domain should win
        assertEquals("review", GoogleSearchFetcher.classifyResult(
                "Acme vs Competitor on Trustpilot", "Compare reviews", "https://trustpilot.com/review/acme"));
    }

    @Test
    void classifiesGeneralContent() {
        assertEquals("general", GoogleSearchFetcher.classifyResult(
                "Acme Product Page", "Learn about Acme features", "https://acme.com/features"));
    }

    @Test
    void capturesQueryAndSnippetFields() {
        GoogleSearchFetcher fetcher = fakeGoogle(200, """
                {
                  "organic_results": [
                    {
                      "title": "Acme Product Review",
                      "snippet": "Acme offers great value for teams.",
                      "link": "https://example.com/review"
                    }
                  ]
                }
                """);

        List<GoogleSearchInsight> results = fetcher.fetch("Acme", "test-key");

        assertFalse(results.isEmpty());
        GoogleSearchInsight first = results.get(0);
        assertTrue(first.getQuery().contains("Acme"));
        assertEquals("Acme Product Review", first.getTitle());
        assertEquals("Acme offers great value for teams.", first.getSnippet());
        assertEquals("https://example.com/review", first.getUrl());
    }

    @Test
    void returnsEmptyListOnNon200() {
        GoogleSearchFetcher fetcher = fakeGoogle(429, """
                { "error": "rate limited" }
                """);
        assertTrue(fetcher.fetch("Acme", "test-key").isEmpty());
    }

    @Test
    void returnsEmptyListOnMissingOrganicResults() {
        GoogleSearchFetcher fetcher = fakeGoogle(200, """
                { "search_metadata": {} }
                """);
        assertTrue(fetcher.fetch("Acme", "test-key").isEmpty());
    }

    @Test
    void runsThreeQueries() {
        AtomicInteger callCount = new AtomicInteger(0);
        GoogleSearchFetcher fetcher = new GoogleSearchFetcher(url -> {
            callCount.incrementAndGet();
            return new HttpFetcher.Response(200, """
                    { "organic_results": [{ "title": "T", "snippet": "S", "link": "https://x.com" }] }
                    """);
        });

        List<GoogleSearchInsight> results = fetcher.fetch("Acme", "test-key");

        assertEquals(3, callCount.get(), "Should execute 3 queries (reviews, pricing, competitors)");
        assertEquals(3, results.size(), "3 queries × 1 result = 3 total");
    }

    @Test
    void continuesOnPartialFailure() {
        AtomicInteger callCount = new AtomicInteger(0);
        GoogleSearchFetcher fetcher = new GoogleSearchFetcher(url -> {
            int n = callCount.incrementAndGet();
            if (n == 2) throw new RuntimeException("network error");
            return new HttpFetcher.Response(200, """
                    { "organic_results": [{ "title": "T", "snippet": "S", "link": "https://x.com" }] }
                    """);
        });

        List<GoogleSearchInsight> results = fetcher.fetch("Acme", "test-key");

        assertEquals(3, callCount.get(), "Should attempt all 3 queries");
        assertEquals(2, results.size(), "2 successful queries × 1 result = 2 total");
    }

    @Test
    void returnsEmptyOnHttpException() {
        GoogleSearchFetcher fetcher = new GoogleSearchFetcher(url -> { throw new RuntimeException("timeout"); });
        assertTrue(fetcher.fetch("Acme", "test-key").isEmpty());
    }

    private GoogleSearchFetcher fakeGoogle(int statusCode, String body) {
        return new GoogleSearchFetcher(url -> new HttpFetcher.Response(statusCode, body));
    }
}
