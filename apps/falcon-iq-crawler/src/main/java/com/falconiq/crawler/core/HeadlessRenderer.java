package com.falconiq.crawler.core;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * HTTP client that calls the analyzer's Playwright render endpoint
 * to get fully-rendered HTML for JS-heavy pages.
 */
public class HeadlessRenderer {

    private static final Logger logger = Logger.getLogger(HeadlessRenderer.class.getName());
    private static final Duration TIMEOUT = Duration.ofSeconds(45);
    private static final ObjectMapper mapper = new ObjectMapper();

    private final String renderEndpointUrl;
    private final HttpClient httpClient;

    public HeadlessRenderer(String analyzerApiUrl) {
        this.renderEndpointUrl = analyzerApiUrl.replaceAll("/+$", "") + "/render";
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(TIMEOUT)
                .build();
    }

    /**
     * Send a URL to the Playwright renderer and return the full HTML, or null on failure.
     */
    public String render(String url) {
        try {
            byte[] body = mapper.writeValueAsBytes(Map.of(
                    "url", url,
                    "timeout_ms", 30000,
                    "wait_until", "networkidle"
            ));

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(renderEndpointUrl))
                    .header("Content-Type", "application/json")
                    .timeout(TIMEOUT)
                    .POST(HttpRequest.BodyPublishers.ofByteArray(body))
                    .build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() < 200 || response.statusCode() >= 300) {
                logger.warning("Render endpoint returned " + response.statusCode() + " for " + url);
                return null;
            }

            JsonNode json = mapper.readTree(response.body());
            if (json.has("html")) {
                logger.info("JS-rendered: " + url);
                return json.get("html").asText();
            }
            return null;

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return null;
        } catch (Exception e) {
            logger.log(Level.WARNING, "Headless render failed for " + url, e);
            return null;
        }
    }
}
