package com.falconiq.crawler.core;

import com.falconiq.crawler.storage.StorageService;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

/**
 * Fetches web pages and delegates storage to a StorageService.
 */
public class PageFetcher {

    private static final String USER_AGENT = "FalconIQCrawler/1.0";
    private static final Duration TIMEOUT = Duration.ofSeconds(10);

    private final HttpClient httpClient;
    private final StorageService storageService;
    private final String crawlId;

    public PageFetcher(StorageService storageService, String crawlId) {
        this.storageService = storageService;
        this.crawlId = crawlId;
        this.httpClient = HttpClient.newBuilder()
                .followRedirects(HttpClient.Redirect.NORMAL)
                .connectTimeout(TIMEOUT)
                .build();
    }

    /**
     * Fetch a URL. Returns a FetchResult with body and storage path, or null on failure.
     */
    public FetchResult fetch(String url) {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(url))
                    .header("User-Agent", USER_AGENT)
                    .timeout(TIMEOUT)
                    .GET()
                    .build();

            HttpResponse<String> response = httpClient.send(request,
                    HttpResponse.BodyHandlers.ofString());
            int status = response.statusCode();

            if (status < 200 || status >= 300) {
                return null;
            }

            String contentType = response.headers()
                    .firstValue("Content-Type").orElse("");
            if (!contentType.contains("text/html")) {
                return null;
            }

            String body = response.body();
            String storagePath = storageService.savePage(crawlId, url, body);
            return new FetchResult(body, storagePath, status);

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return null;
        } catch (Exception e) {
            return null;
        }
    }

    /**
     * Result of fetching a single page.
     */
    public record FetchResult(String html, String storagePath, int statusCode) {
    }
}
