package com.falconiq.crawler.core;

import com.falconiq.crawler.storage.StorageService;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Set;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Multi-threaded web crawler that downloads pages from a single domain using BFS.
 */
public class WebCrawler {

    private static final Logger logger = Logger.getLogger(WebCrawler.class.getName());

    private final String startUrl;
    private final String targetHost;
    private final int maxPages;
    private final int threadCount;
    private final long delayMs;
    private final StorageService storageService;
    private final String crawlId;

    private final Set<String> visited = ConcurrentHashMap.newKeySet();
    private final ConcurrentLinkedQueue<String> frontier = new ConcurrentLinkedQueue<>();
    private final List<CrawlResult> results = Collections.synchronizedList(new ArrayList<>());
    private final AtomicInteger downloadedCount;

    private LinkExtractor linkExtractor;
    private PageFetcher pageFetcher;
    private final Set<String> disallowedPaths = ConcurrentHashMap.newKeySet();

    public WebCrawler(String startUrl, int maxPages, int threadCount, long delayMs,
                      StorageService storageService, String crawlId,
                      AtomicInteger progressCounter) {
        this.startUrl = startUrl;
        this.maxPages = maxPages;
        this.threadCount = threadCount;
        this.delayMs = delayMs;
        this.storageService = storageService;
        this.crawlId = crawlId;
        this.downloadedCount = progressCounter;

        URI uri = URI.create(startUrl);
        this.targetHost = uri.getHost();
    }

    /**
     * Run the crawl and return the list of downloaded pages.
     */
    public List<CrawlResult> crawl() {
        this.pageFetcher = new PageFetcher(storageService, crawlId);
        this.linkExtractor = new LinkExtractor(targetHost);

        loadRobotsTxt();

        String normalized = normalizeStartUrl(startUrl);
        frontier.add(normalized);
        visited.add(normalized);

        logger.info("Starting crawl of " + targetHost
                + " (max " + maxPages + " pages, " + threadCount + " threads)");

        ExecutorService executor = Executors.newFixedThreadPool(threadCount);
        List<Future<?>> activeTasks = new ArrayList<>();

        while (downloadedCount.get() < maxPages) {
            String url;
            while ((url = frontier.poll()) != null && downloadedCount.get() < maxPages) {
                if (isDisallowed(url)) {
                    logger.fine("Blocked by robots.txt: " + url);
                    continue;
                }
                final String targetUrl = url;
                Future<?> future = executor.submit(() -> processUrl(targetUrl));
                activeTasks.add(future);
            }

            activeTasks.removeIf(Future::isDone);

            if (frontier.isEmpty() && activeTasks.isEmpty()) {
                break;
            }

            try {
                Thread.sleep(100);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }

        executor.shutdown();
        try {
            executor.awaitTermination(60, TimeUnit.SECONDS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            executor.shutdownNow();
        }

        logger.info("Crawl " + crawlId + " complete. Downloaded "
                + results.size() + " pages.");
        return results;
    }

    private void processUrl(String url) {
        if (downloadedCount.get() >= maxPages) {
            return;
        }

        if (delayMs > 0) {
            try {
                Thread.sleep(delayMs);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return;
            }
        }

        PageFetcher.FetchResult result = pageFetcher.fetch(url);
        if (result == null) {
            return;
        }

        int count = downloadedCount.incrementAndGet();
        if (count > maxPages) {
            return;
        }

        results.add(new CrawlResult(url, result.storagePath(), result.statusCode()));
        logger.info("[" + count + "/" + maxPages + "] " + url);

        List<String> links = linkExtractor.extract(url, result.html());
        for (String link : links) {
            if (visited.add(link)) {
                frontier.add(link);
            }
        }
    }

    private void loadRobotsTxt() {
        try {
            URI uri = URI.create(startUrl);
            String robotsUrl = uri.getScheme() + "://" + targetHost + "/robots.txt";

            HttpClient client = HttpClient.newBuilder()
                    .connectTimeout(Duration.ofSeconds(5))
                    .build();
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(robotsUrl))
                    .header("User-Agent", "FalconIQCrawler/1.0")
                    .timeout(Duration.ofSeconds(5))
                    .GET()
                    .build();

            HttpResponse<String> response = client.send(request,
                    HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() == 200) {
                parseRobotsTxt(response.body());
                logger.info("Loaded robots.txt from " + robotsUrl);
            }
        } catch (Exception e) {
            logger.warning("Could not fetch robots.txt — proceeding without it");
        }
    }

    private void parseRobotsTxt(String content) {
        boolean relevantSection = false;
        for (String line : content.split("\n")) {
            line = line.trim();
            if (line.startsWith("#") || line.isEmpty()) {
                continue;
            }
            if (line.toLowerCase().startsWith("user-agent:")) {
                String agent = line.substring("user-agent:".length()).trim();
                relevantSection = agent.equals("*")
                        || agent.equalsIgnoreCase("FalconIQCrawler");
            } else if (relevantSection && line.toLowerCase().startsWith("disallow:")) {
                String path = line.substring("disallow:".length()).trim();
                if (!path.isEmpty()) {
                    disallowedPaths.add(path);
                }
            }
        }
    }

    private boolean isDisallowed(String url) {
        try {
            String path = URI.create(url).getPath();
            if (path == null) path = "/";
            for (String disallowed : disallowedPaths) {
                if (path.startsWith(disallowed)) {
                    return true;
                }
            }
        } catch (Exception e) {
            // ignore
        }
        return false;
    }

    private String normalizeStartUrl(String url) {
        try {
            URI uri = URI.create(url);
            String scheme = uri.getScheme() != null ? uri.getScheme() : "https";
            String path = uri.getPath();
            if (path == null || path.isEmpty()) path = "/";
            else if (path.length() > 1 && path.endsWith("/")) {
                path = path.substring(0, path.length() - 1);
            }
            return new URI(scheme, null, uri.getHost(), uri.getPort(),
                    path, uri.getQuery(), null).toString();
        } catch (Exception e) {
            return url;
        }
    }
}
