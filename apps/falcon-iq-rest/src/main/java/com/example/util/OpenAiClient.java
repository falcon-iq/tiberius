package com.example.util;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

public final class OpenAiClient {

    private static final Logger logger = Logger.getLogger(OpenAiClient.class.getName());
    private static final ObjectMapper mapper = new ObjectMapper();
    private static final String OPENAI_API_URL = "https://api.openai.com/v1/chat/completions";
    private static final String SYSTEM_PROMPT =
            "Given a company website, return exactly 5 competitor domains as a JSON object: "
            + "{\"competitors\": [\"domain1.com\", \"domain2.com\", ...]}. Return only the JSON, no other text.";

    private OpenAiClient() {
    }

    public static List<String> suggestCompetitors(String companyUrl) {
        String apiKey = System.getenv("OPENAI_API_KEY");
        if (apiKey == null || apiKey.isBlank()) {
            throw new IllegalStateException("OPENAI_API_KEY environment variable is not configured");
        }

        String normalizedDomain = UrlUtils.normalizeUrl(companyUrl);
        logger.info("Suggesting competitors for: " + normalizedDomain
                + " (API key starts with: " + apiKey.substring(0, Math.min(8, apiKey.length())) + "...)");

        try {
            Map<String, Object> requestMap = Map.of(
                    "model", "gpt-4o-mini",
                    "temperature", 0.3,
                    "messages", List.of(
                            Map.of("role", "system", "content", SYSTEM_PROMPT),
                            Map.of("role", "user", "content", normalizedDomain)
                    )
            );
            String requestBody = mapper.writeValueAsString(requestMap);

            HttpClient httpClient = HttpClient.newBuilder()
                    .connectTimeout(Duration.ofSeconds(10))
                    .build();

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(OPENAI_API_URL))
                    .header("Content-Type", "application/json")
                    .header("Authorization", "Bearer " + apiKey)
                    .timeout(Duration.ofSeconds(30))
                    .POST(HttpRequest.BodyPublishers.ofString(requestBody))
                    .build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() != 200) {
                logger.warning("OpenAI API returned status " + response.statusCode() + ": " + response.body());
                throw new RuntimeException("OpenAI API error: HTTP " + response.statusCode());
            }

            JsonNode root = mapper.readTree(response.body());
            String content = root.at("/choices/0/message/content").asText();

            JsonNode parsed = mapper.readTree(content);
            JsonNode competitorsNode = parsed.get("competitors");

            List<String> competitors = new ArrayList<>();
            if (competitorsNode != null && competitorsNode.isArray()) {
                for (JsonNode node : competitorsNode) {
                    String domain = UrlUtils.normalizeUrl(node.asText());
                    if (!domain.isBlank()) {
                        competitors.add(domain);
                    }
                }
            }

            logger.info("Suggested " + competitors.size() + " competitors for " + normalizedDomain);
            return competitors;

        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Failed to call OpenAI API", e);
            throw new RuntimeException("Failed to get competitor suggestions: " + e.getMessage(), e);
        }
    }
}
