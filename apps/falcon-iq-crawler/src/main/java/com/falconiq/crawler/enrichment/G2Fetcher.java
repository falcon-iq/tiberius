package com.falconiq.crawler.enrichment;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Fetches G2 review data for a company.
 *
 * <p>Strategy:
 * <ol>
 *   <li>SerpAPI search to find the G2 product URL + rating + review count</li>
 *   <li>Playwright rendering of the G2 page to get full review HTML</li>
 *   <li>JSoup parsing for real pros, cons, reviewer info</li>
 *   <li>Fallback to SerpAPI snippets for pros/cons if Playwright is unavailable</li>
 * </ol>
 */
public class G2Fetcher {

    private static final Logger logger = Logger.getLogger(G2Fetcher.class.getName());
    private static final ObjectMapper mapper = new ObjectMapper();
    private static final G2PageParser pageParser = new G2PageParser();

    static final Pattern RATING_PATTERN = Pattern.compile("(\\d+\\.\\d+)\\s*(?:out of|/)\\s*5");
    static final Pattern REVIEW_COUNT_PATTERN = Pattern.compile("(\\d[\\d,]*)\\s*reviews?");

    private final HttpFetcher httpFetcher;
    private final String analyzerApiUrl;

    public G2Fetcher() {
        this(HttpFetcher.createDefault(), "");
    }

    public G2Fetcher(String analyzerApiUrl) {
        this(HttpFetcher.createDefault(), analyzerApiUrl);
    }

    G2Fetcher(HttpFetcher httpFetcher) {
        this(httpFetcher, "");
    }

    G2Fetcher(HttpFetcher httpFetcher, String analyzerApiUrl) {
        this.httpFetcher = httpFetcher;
        this.analyzerApiUrl = analyzerApiUrl != null ? analyzerApiUrl : "";
    }

    /**
     * Fetch G2 data for a company. Returns null if no data found or on error.
     */
    public G2Data fetch(String companyName, String serpApiKey) {
        if (serpApiKey == null || serpApiKey.isBlank()) {
            logger.fine("No SerpAPI key — skipping G2 fetch");
            return null;
        }

        try {
            // Step 1: Find G2 URL + rating via SerpAPI
            SerpResult serp = findG2Product(companyName, serpApiKey);
            if (serp == null) {
                logger.info("No G2 page found for " + companyName);
                return null;
            }

            // Step 2: Try Playwright rendering for full review data
            G2Data data = tryPlaywrightFetch(serp.url);

            // Step 3: If Playwright didn't yield reviews, use SerpAPI snippets (the common path)
            if (data == null || (data.getProsThemes().isEmpty() && data.getConsThemes().isEmpty())) {
                if (data == null) {
                    data = new G2Data();
                    data.setG2Url(serp.url);
                }
                String slug = extractSlug(serp.url);
                if (slug != null) {
                    data.setProsThemes(fetchReviewSnippets(slug, "like best", "positive", serpApiKey));
                    data.setConsThemes(fetchReviewSnippets(slug, "dislike", "negative", serpApiKey));
                }
            }

            // Fill in SerpAPI data as fallback for rating/count/description
            if (data.getRating() == null && serp.rating != null) data.setRating(serp.rating);
            if (data.getReviewCount() == 0 && serp.reviewCount > 0) data.setReviewCount(serp.reviewCount);
            if (data.getDescription().isEmpty() && serp.snippet != null) data.setDescription(serp.snippet);

            return data;
        } catch (Exception e) {
            logger.log(Level.WARNING, "G2 fetch failed for " + companyName, e);
            return null;
        }
    }

    // ── Step 1: SerpAPI discovery ────────────────────────────────────

    private SerpResult findG2Product(String companyName, String serpApiKey) throws Exception {
        String[] queries = {
                "site:g2.com " + companyName + " reviews",
                companyName + " g2 reviews rating"
        };

        for (String query : queries) {
            JsonNode results = runSearch(query, serpApiKey, 5);
            if (results == null) continue;

            for (JsonNode result : results) {
                String link = result.has("link") ? result.get("link").asText() : "";
                if (!link.contains("g2.com/products/")) continue;

                SerpResult sr = new SerpResult();
                sr.url = link;
                sr.snippet = result.has("snippet") ? result.get("snippet").asText() : null;

                JsonNode detected = result.path("rich_snippet").path("top").path("detected_extensions");
                if (detected.has("rating")) sr.rating = detected.get("rating").asDouble();
                if (detected.has("reviews")) sr.reviewCount = detected.get("reviews").asInt();

                if (sr.rating == null && sr.snippet != null) {
                    Matcher m = RATING_PATTERN.matcher(sr.snippet);
                    if (m.find()) sr.rating = Double.parseDouble(m.group(1));
                }
                if (sr.reviewCount == 0 && sr.snippet != null) {
                    Matcher m = REVIEW_COUNT_PATTERN.matcher(sr.snippet);
                    if (m.find()) sr.reviewCount = Integer.parseInt(m.group(1).replace(",", ""));
                }

                return sr;
            }
        }
        return null;
    }

    // ── Step 2: Playwright rendering ─────────────────────────────────

    private G2Data tryPlaywrightFetch(String g2Url) {
        if (analyzerApiUrl.isBlank()) {
            logger.fine("No analyzer API URL configured — skipping Playwright render");
            return null;
        }

        try {
            String renderUrl = analyzerApiUrl.replaceAll("/+$", "") + "/render";
            String body = mapper.writeValueAsString(java.util.Map.of(
                    "url", g2Url,
                    "timeout_ms", 30000,
                    "wait_until", "networkidle"
            ));

            // Use a direct HTTP call instead of HttpFetcher (POST with JSON body)
            java.net.http.HttpClient client = java.net.http.HttpClient.newBuilder()
                    .connectTimeout(java.time.Duration.ofSeconds(10))
                    .build();
            java.net.http.HttpRequest request = java.net.http.HttpRequest.newBuilder()
                    .uri(java.net.URI.create(renderUrl))
                    .header("Content-Type", "application/json")
                    .timeout(java.time.Duration.ofSeconds(45))
                    .POST(java.net.http.HttpRequest.BodyPublishers.ofString(body))
                    .build();

            java.net.http.HttpResponse<String> response = client.send(request,
                    java.net.http.HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() < 200 || response.statusCode() >= 300) {
                logger.warning("Playwright render returned " + response.statusCode() + " for " + g2Url);
                return null;
            }

            JsonNode json = mapper.readTree(response.body());
            if (!json.has("html")) return null;

            String html = json.get("html").asText();
            logger.info("Playwright rendered G2 page: " + g2Url + " (" + html.length() + " chars)");
            return pageParser.parse(html, g2Url);

        } catch (Exception e) {
            logger.log(Level.WARNING, "Playwright render failed for " + g2Url, e);
            return null;
        }
    }

    // ── Step 3: SerpAPI snippet fallback ─────────────────────────────

    private List<G2Data.ReviewTheme> fetchReviewSnippets(String slug, String phrase,
                                                          String sentiment, String serpApiKey) {
        List<G2Data.ReviewTheme> themes = new ArrayList<>();
        try {
            String query = "site:g2.com/products/" + slug + "/reviews \"What do you " + phrase + "\"";
            JsonNode results = runSearch(query, serpApiKey, 10);
            if (results == null) return themes;

            for (JsonNode result : results) {
                String snippet = result.has("snippet") ? result.get("snippet").asText() : "";
                if (snippet.isBlank()) continue;

                String answer = extractAnswerFromSnippet(snippet, phrase);
                if (answer != null && answer.length() >= 15) {
                    boolean duplicate = themes.stream().anyMatch(t -> t.getTheme().equals(answer));
                    if (!duplicate) {
                        themes.add(new G2Data.ReviewTheme(answer, sentiment));
                    }
                }
            }
        } catch (Exception e) {
            logger.log(Level.FINE, "G2 " + phrase + " snippet fetch failed for " + slug, e);
        }
        return themes.stream().limit(10).toList();
    }

    // ── Helpers ──────────────────────────────────────────────────────

    static String extractAnswerFromSnippet(String snippet, String phrase) {
        String lower = snippet.toLowerCase();
        int qIdx = lower.indexOf(phrase);
        if (qIdx < 0) return null;

        int questionEnd = snippet.indexOf('?', qIdx);
        if (questionEnd < 0) return null;

        String answer = snippet.substring(questionEnd + 1).trim();

        int nextQ = answer.toLowerCase().indexOf("what do you");
        if (nextQ > 0) {
            answer = answer.substring(0, nextQ).trim();
        }

        return answer.isBlank() ? null : answer;
    }

    static String extractSlug(String g2Url) {
        if (g2Url == null) return null;
        int idx = g2Url.indexOf("/products/");
        if (idx < 0) return null;
        String rest = g2Url.substring(idx + "/products/".length());
        int slash = rest.indexOf('/');
        return slash > 0 ? rest.substring(0, slash) : rest;
    }

    private JsonNode runSearch(String query, String serpApiKey, int num) throws Exception {
        String encoded = URLEncoder.encode(query, StandardCharsets.UTF_8);
        String url = "https://serpapi.com/search.json?engine=google&q=" + encoded
                + "&api_key=" + serpApiKey + "&num=" + num;

        HttpFetcher.Response response = httpFetcher.get(url);
        if (response.statusCode() != 200) {
            logger.warning("SerpAPI returned " + response.statusCode() + " for: " + query);
            return null;
        }

        JsonNode root = mapper.readTree(response.body());
        JsonNode organicResults = root.get("organic_results");
        if (organicResults == null || !organicResults.isArray() || organicResults.isEmpty()) {
            return null;
        }
        return organicResults;
    }

    private static class SerpResult {
        String url;
        String snippet;
        Double rating;
        int reviewCount;
    }
}
