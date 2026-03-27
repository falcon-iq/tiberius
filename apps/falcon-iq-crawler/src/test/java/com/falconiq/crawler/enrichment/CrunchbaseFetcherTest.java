package com.falconiq.crawler.enrichment;

import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class CrunchbaseFetcherTest {

    @Test
    void returnsNullWhenNoApiKey() {
        CrunchbaseFetcher fetcher = new CrunchbaseFetcher(url -> { throw new AssertionError("Should not call HTTP"); });
        assertNull(fetcher.fetch("Acme", null));
        assertNull(fetcher.fetch("Acme", ""));
        assertNull(fetcher.fetch("Acme", "   "));
    }

    @Test
    void extractsDataFromKnowledgeGraph() {
        String kgResponse = """
                {
                  "knowledge_graph": {
                    "title": "Stripe, Inc.",
                    "type": "Financial services company",
                    "founded": "2010, San Francisco, CA",
                    "headquarters": "Dublin, Ireland",
                    "number_of_employees": "8,500 (2025)",
                    "valuation": "$159 billion"
                  },
                  "organic_results": []
                }
                """;

        CrunchbaseFetcher fetcher = fakeSequential(
                new FakeResponse(200, kgResponse),
                new FakeResponse(200, """
                        { "organic_results": [] }
                        """)
        );

        CrunchbaseData result = fetcher.fetch("Stripe", "test-key");

        assertNotNull(result);
        assertEquals("2010, San Francisco, CA", result.getFounded());
        assertEquals("Dublin, Ireland", result.getHq());
        assertEquals("8,500 (2025)", result.getEmployeeCount());
        assertEquals("$159 billion", result.getTotalFunding());
    }

    @Test
    void extractsFundingFromSnippets() {
        CrunchbaseFetcher fetcher = fakeSequential(
                new FakeResponse(200, """
                        { "organic_results": [] }
                        """),
                new FakeResponse(200, """
                        {
                          "organic_results": [
                            {
                              "title": "Acme Funding",
                              "snippet": "Acme has raised a total of $705.3 million across 4 funding rounds."
                            }
                          ]
                        }
                        """)
        );

        CrunchbaseData result = fetcher.fetch("Acme", "test-key");

        assertNotNull(result);
        assertEquals("$705.3M", result.getTotalFunding());
    }

    @Test
    void extractsEmployeesFromSnippets() {
        CrunchbaseFetcher fetcher = fakeSequential(
                new FakeResponse(200, """
                        { "organic_results": [] }
                        """),
                new FakeResponse(200, """
                        {
                          "organic_results": [
                            {
                              "snippet": "13,000 people work at Stripe across 20 global offices."
                            }
                          ]
                        }
                        """)
        );

        CrunchbaseData result = fetcher.fetch("Stripe", "test-key");

        assertNotNull(result);
        assertEquals("13,000", result.getEmployeeCount());
    }

    @Test
    void returnsNullWhenNoDataFound() {
        CrunchbaseFetcher fetcher = fakeSequential(
                new FakeResponse(200, """
                        { "organic_results": [] }
                        """),
                new FakeResponse(200, """
                        { "organic_results": [] }
                        """)
        );

        assertNull(fetcher.fetch("xyznonexistent12345", "test-key"));
    }

    @Test
    void returnsNullOnHttpError() {
        CrunchbaseFetcher fetcher = new CrunchbaseFetcher(url -> new HttpFetcher.Response(429, "rate limited"));
        assertNull(fetcher.fetch("Acme", "test-key"));
    }

    @Test
    void returnsNullOnException() {
        CrunchbaseFetcher fetcher = new CrunchbaseFetcher(url -> { throw new RuntimeException("timeout"); });
        assertNull(fetcher.fetch("Acme", "test-key"));
    }

    // ── extractFunding ──────────────────────────────────────────────

    @Test
    void extractsFundingBillions() {
        assertEquals("$2.5B", CrunchbaseFetcher.extractFunding("raised $2.5 billion in funding"));
    }

    @Test
    void extractsFundingMillions() {
        assertEquals("$705.3M", CrunchbaseFetcher.extractFunding("total of $705.3 million across rounds"));
    }

    @Test
    void extractsFundingShortForm() {
        assertEquals("$1.2B", CrunchbaseFetcher.extractFunding("valued at $1.2B"));
        assertEquals("$50.0M", CrunchbaseFetcher.extractFunding("raised $50M"));
    }

    @Test
    void returnsNullForNoFunding() {
        assertNull(CrunchbaseFetcher.extractFunding("the company has many employees"));
    }

    // ── Helpers ─────────────────────────────────────────────────────

    private record FakeResponse(int statusCode, String body) {}

    private CrunchbaseFetcher fakeSequential(FakeResponse... responses) {
        List<FakeResponse> queue = new ArrayList<>(List.of(responses));
        int[] idx = {0};
        return new CrunchbaseFetcher(url -> {
            FakeResponse r = queue.get(Math.min(idx[0]++, queue.size() - 1));
            return new HttpFetcher.Response(r.statusCode(), r.body());
        });
    }
}
