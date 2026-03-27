package com.falconiq.crawler.enrichment;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Fetches review ratings from multiple third-party sites (Capterra, TrustRadius,
 * Trustpilot, GetApp, PeerSpot) via SerpAPI.
 */
public class ReviewSiteFetcher {

    private static final Logger logger = Logger.getLogger(ReviewSiteFetcher.class.getName());
    private static final ObjectMapper mapper = new ObjectMapper();

    private static final Pattern RATING_PATTERN = Pattern.compile("(\\d+\\.?\\d*)\\s*(?:out of|/)\\s*(?:5|10)");
    private static final Pattern REVIEW_COUNT_PATTERN = Pattern.compile("(\\d[\\d,]*)\\s*reviews?");
    private static final Pattern STAR_PATTERN = Pattern.compile("(\\d+\\.?\\d*)\\s*stars?");

    private static final Map<String, String> REVIEW_SITES = Map.of(
            "capterra.com", "capterra",
            "trustradius.com", "trustradius",
            "trustpilot.com", "trustpilot",
            "getapp.com", "getapp",
            "peerspot.com", "peerspot",
            "softwareadvice.com", "softwareadvice"
    );

    private final HttpFetcher httpFetcher;

    public ReviewSiteFetcher() {
        this(HttpFetcher.createDefault());
    }

    ReviewSiteFetcher(HttpFetcher httpFetcher) {
        this.httpFetcher = httpFetcher;
    }

    /**
     * Fetch review data from third-party review sites for a company.
     * Uses a single SerpAPI call to find results across multiple review platforms.
     */
    public List<ReviewSiteData> fetch(String companyName, String serpApiKey) {
        if (serpApiKey == null || serpApiKey.isBlank()) {
            return List.of();
        }

        List<ReviewSiteData> results = new ArrayList<>();

        try {
            String sites = "capterra.com OR trustradius.com OR trustpilot.com OR getapp.com OR peerspot.com";
            String query = companyName + " reviews (" + sites + ")";
            String encoded = URLEncoder.encode(query, StandardCharsets.UTF_8);
            String url = "https://serpapi.com/search.json?engine=google&q=" + encoded
                    + "&api_key=" + serpApiKey + "&num=10";

            HttpFetcher.Response response = httpFetcher.get(url);
            if (response.statusCode() != 200) {
                logger.warning("SerpAPI returned " + response.statusCode() + " for review site search");
                return results;
            }

            JsonNode root = mapper.readTree(response.body());
            JsonNode organicResults = root.get("organic_results");
            if (organicResults == null || !organicResults.isArray()) {
                return results;
            }

            // Track which sites we've already captured (one per site)
            java.util.Set<String> seen = new java.util.HashSet<>();

            for (JsonNode result : organicResults) {
                String link = result.has("link") ? result.get("link").asText() : "";
                String snippet = result.has("snippet") ? result.get("snippet").asText() : "";
                String title = result.has("title") ? result.get("title").asText() : "";

                String siteName = identifySite(link);
                if (siteName == null || seen.contains(siteName)) continue;

                ReviewSiteData data = new ReviewSiteData();
                data.setSiteName(siteName);
                data.setUrl(link);
                data.setSnippet(snippet);

                // Try structured rich snippet first
                JsonNode richSnippet = result.get("rich_snippet");
                if (richSnippet != null) {
                    JsonNode detected = richSnippet.path("top").path("detected_extensions");
                    if (detected.has("rating")) {
                        data.setRating(detected.get("rating").asDouble());
                    }
                    if (detected.has("reviews")) {
                        data.setReviewCount(detected.get("reviews").asInt());
                    }
                }

                // Fallback: regex on snippet/title
                if (data.getRating() == null) {
                    String text = snippet + " " + title;
                    Matcher rm = RATING_PATTERN.matcher(text);
                    if (rm.find()) {
                        double val = Double.parseDouble(rm.group(1));
                        // Normalize /10 ratings to /5
                        if (text.substring(rm.start()).contains("/10") || text.substring(rm.start()).contains("out of 10")) {
                            val = val / 2.0;
                        }
                        data.setRating(val);
                    } else {
                        Matcher sm = STAR_PATTERN.matcher(text);
                        if (sm.find()) {
                            data.setRating(Double.parseDouble(sm.group(1)));
                        }
                    }
                }

                if (data.getReviewCount() == 0) {
                    Matcher cm = REVIEW_COUNT_PATTERN.matcher(snippet + " " + title);
                    if (cm.find()) {
                        data.setReviewCount(Integer.parseInt(cm.group(1).replace(",", "")));
                    }
                }

                seen.add(siteName);
                results.add(data);
                logger.fine("Found " + siteName + " data: rating=" + data.getRating()
                        + " reviews=" + data.getReviewCount());
            }

        } catch (Exception e) {
            logger.log(Level.WARNING, "Review site fetch failed for " + companyName, e);
        }

        return results;
    }

    private String identifySite(String url) {
        String lower = url.toLowerCase();
        for (Map.Entry<String, String> entry : REVIEW_SITES.entrySet()) {
            if (lower.contains(entry.getKey())) {
                return entry.getValue();
            }
        }
        return null;
    }
}
