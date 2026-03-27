package com.falconiq.crawler.enrichment;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Fetches Google Search insights for a company via SerpAPI.
 * Runs targeted queries (reviews, pricing, competitors) and classifies results.
 */
public class GoogleSearchFetcher {

    private static final Logger logger = Logger.getLogger(GoogleSearchFetcher.class.getName());
    private static final ObjectMapper mapper = new ObjectMapper();

    private final HttpFetcher httpFetcher;

    public GoogleSearchFetcher() {
        this(HttpFetcher.createDefault());
    }

    GoogleSearchFetcher(HttpFetcher httpFetcher) {
        this.httpFetcher = httpFetcher;
    }

    private static final Set<String> REVIEW_DOMAINS = Set.of(
            "g2.com", "capterra.com", "trustradius.com", "trustpilot.com",
            "getapp.com", "softwareadvice.com", "peerspot.com"
    );
    private static final Set<String> COMPARISON_KEYWORDS = Set.of(
            " vs ", " versus ", " alternative", " compared to", " competitor"
    );
    private static final Set<String> COMPLAINT_KEYWORDS = Set.of(
            "complaint", "problem", "issue", "terrible", "worst", "scam", "ripoff"
    );

    private static final String[] QUERY_TEMPLATES = {
            "\"%s\" reviews",
            "\"%s\" pricing",
            "\"%s\" vs competitors"
    };

    /**
     * Fetch search insights for a company. Returns empty list on error.
     */
    public List<GoogleSearchInsight> fetch(String companyName, String serpApiKey) {
        if (serpApiKey == null || serpApiKey.isBlank()) {
            logger.fine("No SerpAPI key — skipping Google Search fetch");
            return List.of();
        }

        List<GoogleSearchInsight> allInsights = new ArrayList<>();

        for (String template : QUERY_TEMPLATES) {
            try {
                String query = String.format(template, companyName);
                List<GoogleSearchInsight> insights = executeSearch(query, serpApiKey);
                allInsights.addAll(insights);
            } catch (Exception e) {
                logger.log(Level.WARNING, "Google search failed for query template: " + template, e);
            }
        }

        return allInsights;
    }

    private List<GoogleSearchInsight> executeSearch(String query, String serpApiKey) throws Exception {
        String encoded = URLEncoder.encode(query, StandardCharsets.UTF_8);
        String url = "https://serpapi.com/search.json?engine=google&q=" + encoded
                + "&api_key=" + serpApiKey + "&num=5";

        HttpFetcher.Response response = httpFetcher.get(url);
        if (response.statusCode() != 200) {
            logger.warning("SerpAPI returned " + response.statusCode() + " for query: " + query);
            return List.of();
        }

        JsonNode root = mapper.readTree(response.body());
        JsonNode organicResults = root.get("organic_results");
        if (organicResults == null || !organicResults.isArray()) {
            return List.of();
        }

        List<GoogleSearchInsight> insights = new ArrayList<>();
        for (JsonNode result : organicResults) {
            String title = result.has("title") ? result.get("title").asText() : "";
            String snippet = result.has("snippet") ? result.get("snippet").asText() : "";
            String resultUrl = result.has("link") ? result.get("link").asText() : "";

            String insightType = classifyResult(title, snippet, resultUrl);

            insights.add(new GoogleSearchInsight(query, title, snippet, resultUrl, insightType));
        }

        return insights;
    }

    static String classifyResult(String title, String snippet, String url) {
        String lowerUrl = url.toLowerCase();
        String lowerText = (title + " " + snippet).toLowerCase();

        for (String domain : REVIEW_DOMAINS) {
            if (lowerUrl.contains(domain)) {
                return "review";
            }
        }

        for (String keyword : COMPARISON_KEYWORDS) {
            if (lowerText.contains(keyword)) {
                return "comparison";
            }
        }

        for (String keyword : COMPLAINT_KEYWORDS) {
            if (lowerText.contains(keyword)) {
                return "complaint";
            }
        }

        return "general";
    }
}
