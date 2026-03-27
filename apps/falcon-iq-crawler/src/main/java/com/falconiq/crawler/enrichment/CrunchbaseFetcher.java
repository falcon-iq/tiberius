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
 * Fetches company data (founded, HQ, funding, employees, investors) via SerpAPI.
 *
 * <p>Uses two sources:
 * <ol>
 *   <li>Google Knowledge Graph — structured company facts (founded, HQ, CEO, revenue, employees)</li>
 *   <li>Crunchbase/Google snippets — funding totals, investors, additional details</li>
 * </ol>
 */
public class CrunchbaseFetcher {

    private static final Logger logger = Logger.getLogger(CrunchbaseFetcher.class.getName());
    private static final ObjectMapper mapper = new ObjectMapper();

    private static final Pattern FUNDING_PATTERN = Pattern.compile(
            "\\$([\\d,.]+)\\s*(billion|million|B|M)", Pattern.CASE_INSENSITIVE);
    private static final Pattern EMPLOYEE_PATTERN = Pattern.compile(
            "([\\d,]+)\\s*(?:employees|people|workers|staff)");

    private final HttpFetcher httpFetcher;

    public CrunchbaseFetcher() {
        this(HttpFetcher.createDefault());
    }

    CrunchbaseFetcher(HttpFetcher httpFetcher) {
        this.httpFetcher = httpFetcher;
    }

    /**
     * Fetch company data using SerpAPI. Uses the SerpAPI key (not a Crunchbase key).
     * Returns null if no data found.
     */
    public CrunchbaseData fetch(String companyName, String serpApiKey) {
        if (serpApiKey == null || serpApiKey.isBlank()) {
            logger.fine("No SerpAPI key — skipping company data fetch");
            return null;
        }

        try {
            CrunchbaseData data = new CrunchbaseData();
            boolean hasData = false;

            // Step 1: Google Knowledge Graph (most reliable structured data)
            hasData |= fetchFromKnowledgeGraph(companyName, serpApiKey, data);

            // Step 2: Crunchbase + funding snippets for additional details
            hasData |= fetchFromSnippets(companyName, serpApiKey, data);

            return hasData ? data : null;
        } catch (Exception e) {
            logger.log(Level.WARNING, "Company data fetch failed for " + companyName, e);
            return null;
        }
    }

    private boolean fetchFromKnowledgeGraph(String companyName, String serpApiKey,
                                             CrunchbaseData data) throws Exception {
        String query = companyName + " company";
        String encoded = URLEncoder.encode(query, StandardCharsets.UTF_8);
        String url = "https://serpapi.com/search.json?engine=google&q=" + encoded
                + "&api_key=" + serpApiKey;

        HttpFetcher.Response response = httpFetcher.get(url);
        if (response.statusCode() != 200) {
            logger.warning("SerpAPI returned " + response.statusCode() + " for knowledge graph search");
            return false;
        }

        JsonNode root = mapper.readTree(response.body());
        JsonNode kg = root.get("knowledge_graph");
        if (kg == null) {
            logger.fine("No knowledge graph for " + companyName);
            return false;
        }

        boolean found = false;

        if (data.getFounded() == null && kg.has("founded")) {
            data.setFounded(kg.get("founded").asText());
            found = true;
        }

        if (data.getHq() == null && kg.has("headquarters")) {
            data.setHq(kg.get("headquarters").asText());
            found = true;
        }

        if (data.getEmployeeCount() == null && kg.has("number_of_employees")) {
            data.setEmployeeCount(kg.get("number_of_employees").asText());
            found = true;
        }

        // Total funding from knowledge graph (sometimes present as "valuation")
        if (data.getTotalFunding() == null && kg.has("valuation")) {
            data.setTotalFunding(kg.get("valuation").asText());
            found = true;
        }

        // Founders as investors fallback
        if (kg.has("founders")) {
            String founders = kg.get("founders").asText();
            if (!founders.isBlank() && data.getInvestors().isEmpty()) {
                // Don't add founders as investors — they're different
                // But log for context
                logger.fine("KG founders for " + companyName + ": " + founders);
            }
        }

        logger.info("Knowledge graph for " + companyName + ": founded=" + data.getFounded()
                + " hq=" + data.getHq() + " employees=" + data.getEmployeeCount());
        return found;
    }

    private boolean fetchFromSnippets(String companyName, String serpApiKey,
                                       CrunchbaseData data) throws Exception {
        String query = companyName + " funding raised investors total";
        String encoded = URLEncoder.encode(query, StandardCharsets.UTF_8);
        String url = "https://serpapi.com/search.json?engine=google&q=" + encoded
                + "&api_key=" + serpApiKey + "&num=5";

        HttpFetcher.Response response = httpFetcher.get(url);
        if (response.statusCode() != 200) return false;

        JsonNode root = mapper.readTree(response.body());
        JsonNode results = root.get("organic_results");
        if (results == null || !results.isArray()) return false;

        boolean found = false;
        List<String> investors = new ArrayList<>(data.getInvestors());

        for (JsonNode result : results) {
            String snippet = result.has("snippet") ? result.get("snippet").asText() : "";
            if (snippet.isBlank()) continue;

            // Extract total funding
            if (data.getTotalFunding() == null) {
                String funding = extractFunding(snippet);
                if (funding != null) {
                    data.setTotalFunding(funding);
                    found = true;
                }
            }

            // Extract employee count if not from KG
            if (data.getEmployeeCount() == null) {
                Matcher em = EMPLOYEE_PATTERN.matcher(snippet);
                if (em.find()) {
                    data.setEmployeeCount(em.group(1));
                    found = true;
                }
            }

            // Extract investor names from snippets
            extractInvestors(snippet, investors);
        }

        if (!investors.isEmpty() && data.getInvestors().isEmpty()) {
            data.setInvestors(investors.stream().distinct().limit(10).toList());
            found = true;
        }

        return found;
    }

    static String extractFunding(String text) {
        Matcher m = FUNDING_PATTERN.matcher(text);
        if (!m.find()) return null;

        String numStr = m.group(1).replace(",", "");
        String unit = m.group(2).toLowerCase();

        try {
            double amount = Double.parseDouble(numStr);
            return switch (unit) {
                case "billion", "b" -> String.format("$%.1fB", amount);
                case "million", "m" -> String.format("$%.1fM", amount);
                default -> "$" + numStr;
            };
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private void extractInvestors(String snippet, List<String> investors) {
        // Look for common patterns: "backed by X, Y, and Z" or "investors include X"
        String lower = snippet.toLowerCase();
        int idx = -1;
        for (String trigger : new String[]{"backed by", "investors include", "invested by", "led by"}) {
            idx = lower.indexOf(trigger);
            if (idx >= 0) {
                idx += trigger.length();
                break;
            }
        }
        if (idx < 0) return;

        // Extract the text after the trigger, up to the next sentence
        String rest = snippet.substring(idx).trim();
        int period = rest.indexOf('.');
        if (period > 0) rest = rest.substring(0, period);

        // Split by common delimiters
        String[] parts = rest.split("[,;]|\\band\\b");
        for (String part : parts) {
            String name = part.trim()
                    .replaceAll("^(and|with|from)\\s+", "")
                    .replaceAll("\\s+\\(.*\\)$", "")
                    .trim();
            if (name.length() >= 2 && name.length() <= 60 && Character.isUpperCase(name.charAt(0))) {
                investors.add(name);
            }
        }
    }
}
