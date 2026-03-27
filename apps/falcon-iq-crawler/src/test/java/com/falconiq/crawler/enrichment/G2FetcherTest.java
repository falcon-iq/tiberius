package com.falconiq.crawler.enrichment;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class G2FetcherTest {

    @Test
    void returnsNullWhenNoApiKey() {
        G2Fetcher fetcher = new G2Fetcher(url -> { throw new AssertionError("Should not call HTTP"); });
        assertNull(fetcher.fetch("Acme", null));
        assertNull(fetcher.fetch("Acme", ""));
        assertNull(fetcher.fetch("Acme", "   "));
    }

    @Test
    void extractsRatingFromDetectedExtensions() {
        G2Fetcher fetcher = fakeG2(serpResponse(4.5, 1234));
        G2Data result = fetcher.fetch("Acme", "test-key");

        assertNotNull(result);
        assertEquals(4.5, result.getRating());
        assertEquals(1234, result.getReviewCount());
        assertEquals("https://www.g2.com/products/acme/reviews", result.getG2Url());
    }

    @Test
    void extractsDescriptionFromSnippet() {
        G2Fetcher fetcher = fakeG2(serpResponse(4.0, 100));
        G2Data result = fetcher.fetch("Acme", "test-key");

        assertNotNull(result);
        assertEquals("Acme product overview from G2.", result.getDescription());
    }

    @Test
    void parsesRatingFromSnippetFallback() {
        String serp = """
                {
                  "organic_results": [
                    {
                      "title": "Acme Reviews",
                      "snippet": "Acme has a rating of 4.2 out of 5 based on 500 reviews.",
                      "link": "https://www.g2.com/products/acme/reviews"
                    }
                  ]
                }
                """;
        G2Fetcher fetcher = fakeG2(serp);
        G2Data result = fetcher.fetch("Acme", "test-key");

        assertNotNull(result);
        assertEquals(4.2, result.getRating());
        assertEquals(500, result.getReviewCount());
    }

    @Test
    void returnsNullOnEmptyResults() {
        G2Fetcher fetcher = fakeG2("""
                { "organic_results": [] }
                """);
        assertNull(fetcher.fetch("Acme", "test-key"));
    }

    @Test
    void returnsNullOnNoG2Link() {
        G2Fetcher fetcher = fakeG2("""
                {
                  "organic_results": [
                    { "title": "Acme", "snippet": "...", "link": "https://acme.com" }
                  ]
                }
                """);
        assertNull(fetcher.fetch("Acme", "test-key"));
    }

    @Test
    void returnsNullOnNon200() {
        G2Fetcher fetcher = new G2Fetcher(url -> new HttpFetcher.Response(429, "rate limited"));
        assertNull(fetcher.fetch("Acme", "test-key"));
    }

    @Test
    void returnsNullOnHttpException() {
        G2Fetcher fetcher = new G2Fetcher(url -> { throw new RuntimeException("timeout"); });
        assertNull(fetcher.fetch("Acme", "test-key"));
    }

    // ── extractAnswerFromSnippet ────────────────────────────────────

    @Test
    void extractsAnswerAfterQuestion() {
        String snippet = "What do you like best about Slack? Slack is very smooth and easy to use.";
        assertEquals("Slack is very smooth and easy to use.", G2Fetcher.extractAnswerFromSnippet(snippet, "like best"));
    }

    @Test
    void extractsAnswerAndTruncatesAtSecondQuestion() {
        String snippet = "What do you like best about Slack? Great tool. What do you dislike? Too expensive.";
        assertEquals("Great tool.", G2Fetcher.extractAnswerFromSnippet(snippet, "like best"));
    }

    @Test
    void returnsNullWhenNoQuestionMark() {
        String snippet = "What do you like best about Slack - it is great";
        assertNull(G2Fetcher.extractAnswerFromSnippet(snippet, "like best"));
    }

    @Test
    void returnsNullWhenAnswerIsEmpty() {
        String snippet = "What do you dislike about Slack?";
        assertNull(G2Fetcher.extractAnswerFromSnippet(snippet, "dislike"));
    }

    @Test
    void returnsNullWhenPhraseNotFound() {
        String snippet = "Slack is a great messaging tool.";
        assertNull(G2Fetcher.extractAnswerFromSnippet(snippet, "like best"));
    }

    // ── extractSlug ─────────────────────────────────────────────────

    @Test
    void extractsSlugFromG2Url() {
        assertEquals("slack", G2Fetcher.extractSlug("https://www.g2.com/products/slack/reviews"));
        assertEquals("hubspot", G2Fetcher.extractSlug("https://g2.com/products/hubspot/reviews?page=2"));
        assertNull(G2Fetcher.extractSlug("https://g2.com/categories/crm"));
        assertNull(G2Fetcher.extractSlug(null));
    }

    // ── Helpers ─────────────────────────────────────────────────────

    private G2Fetcher fakeG2(String serpJson) {
        // Returns the same response for all calls (product search + pros/cons searches)
        return new G2Fetcher(url -> new HttpFetcher.Response(200, serpJson));
    }

    private String serpResponse(Double rating, int reviewCount) {
        String richSnippet = "";
        if (rating != null || reviewCount > 0) {
            String ratStr = rating != null ? "\"rating\":" + rating : "";
            String revStr = reviewCount > 0 ? "\"reviews\":" + reviewCount : "";
            String comma = (!ratStr.isEmpty() && !revStr.isEmpty()) ? "," : "";
            richSnippet = """
                    ,"rich_snippet":{"top":{"detected_extensions":{%s%s%s}}}
                    """.formatted(ratStr, comma, revStr);
        }
        return """
                {
                  "organic_results": [
                    {
                      "title": "Acme Reviews",
                      "snippet": "Acme product overview from G2.",
                      "link": "https://www.g2.com/products/acme/reviews"
                      %s
                    }
                  ]
                }
                """.formatted(richSnippet);
    }
}
