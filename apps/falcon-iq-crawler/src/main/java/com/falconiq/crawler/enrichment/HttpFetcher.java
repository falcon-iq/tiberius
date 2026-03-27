package com.falconiq.crawler.enrichment;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

/**
 * Simple HTTP GET abstraction that returns status code + body.
 * Allows test code to provide a fake implementation without mocking HttpClient.
 */
@FunctionalInterface
public interface HttpFetcher {

    record Response(int statusCode, String body) {}

    Response get(String url) throws Exception;

    /**
     * Default production implementation using java.net.http.HttpClient.
     */
    static HttpFetcher createDefault() {
        HttpClient client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(10))
                .followRedirects(HttpClient.Redirect.NORMAL)
                .build();
        return url -> {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(url))
                    .timeout(Duration.ofSeconds(15))
                    .header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                            + "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                    .header("Accept", "text/html,application/xhtml+xml,application/json,*/*")
                    .header("Accept-Language", "en-US,en;q=0.9")
                    .GET()
                    .build();
            HttpResponse<String> resp = client.send(request, HttpResponse.BodyHandlers.ofString());
            return new Response(resp.statusCode(), resp.body());
        };
    }
}
