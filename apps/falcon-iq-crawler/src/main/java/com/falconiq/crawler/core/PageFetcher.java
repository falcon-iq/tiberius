package com.falconiq.crawler.core;

import com.falconiq.crawler.storage.StorageService;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Fetches web pages and delegates storage to a StorageService.
 * Uses Lane A (static JSoup) / Lane B (headless Playwright) pattern:
 * if the initial fetch returns JS-heavy content, re-fetches via headless renderer.
 */
public class PageFetcher {

    private static final Logger logger = Logger.getLogger(PageFetcher.class.getName());
    private static final String USER_AGENT = "FalconIQCrawler/1.0";
    private static final Duration TIMEOUT = Duration.ofSeconds(10);

    private final HttpClient httpClient;
    private final StorageService storageService;
    private final String crawlId;
    private final HeadlessRenderer headlessRenderer;

    public PageFetcher(StorageService storageService, String crawlId) {
        this(storageService, crawlId, null);
    }

    public PageFetcher(StorageService storageService, String crawlId, HeadlessRenderer headlessRenderer) {
        this.storageService = storageService;
        this.crawlId = crawlId;
        this.headlessRenderer = headlessRenderer;
        this.httpClient = HttpClient.newBuilder()
                .followRedirects(HttpClient.Redirect.NORMAL)
                .connectTimeout(TIMEOUT)
                .build();
    }

    /**
     * Fetch a URL. Returns a FetchResult with body and storage path, or null on failure.
     * If the page looks JS-rendered and a headless renderer is available, re-fetches via Playwright.
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

            // Lane B: if JS-heavy, re-fetch with headless renderer
            if (headlessRenderer != null && JsDetector.needsJsRendering(body)) {
                logger.info("JS-heavy page detected, using headless renderer: " + url);
                String rendered = headlessRenderer.render(url);
                if (rendered != null && !rendered.isBlank()) {
                    body = rendered;
                } else {
                    logger.warning("Headless render failed, falling back to static HTML: " + url);
                }
            }

            String storagePath = storageService.savePage(crawlId, url, body);
            return new FetchResult(body, storagePath, status);

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return null;
        } catch (Exception e) {
            logger.log(Level.FINE, "Fetch failed for " + url, e);
            return null;
        }
    }

    /**
     * Result of fetching a single page.
     */
    public record FetchResult(String html, String storagePath, int statusCode) {
    }
}
