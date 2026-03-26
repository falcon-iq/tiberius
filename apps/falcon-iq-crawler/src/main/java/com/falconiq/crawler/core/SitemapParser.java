package com.falconiq.crawler.core;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Logger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Fetches and parses sitemap.xml to discover URLs.
 * Falls back to robots.txt Sitemap directives.
 */
public class SitemapParser {

    private static final Logger logger = Logger.getLogger(SitemapParser.class.getName());
    private static final Duration TIMEOUT = Duration.ofSeconds(10);
    private static final Pattern LOC_PATTERN = Pattern.compile("<loc>\\s*(.*?)\\s*</loc>");
    private static final Pattern SITEMAP_DIRECTIVE = Pattern.compile("(?i)^Sitemap:\\s*(.+)$", Pattern.MULTILINE);

    private final HttpClient httpClient;

    public SitemapParser() {
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(TIMEOUT)
                .followRedirects(HttpClient.Redirect.NORMAL)
                .build();
    }

    /**
     * Discover URLs from sitemap.xml (and any sitemaps referenced in robots.txt).
     */
    public List<String> discoverUrls(String baseUrl, String robotsTxtContent) {
        List<String> urls = new ArrayList<>();

        // 1. Try standard sitemap.xml location
        String sitemapUrl = baseUrl.replaceAll("/+$", "") + "/sitemap.xml";
        urls.addAll(fetchAndParseSitemap(sitemapUrl));

        // 2. Check robots.txt for additional Sitemap directives
        if (robotsTxtContent != null) {
            Matcher m = SITEMAP_DIRECTIVE.matcher(robotsTxtContent);
            while (m.find()) {
                String robotsSitemapUrl = m.group(1).trim();
                if (!robotsSitemapUrl.equals(sitemapUrl)) {
                    urls.addAll(fetchAndParseSitemap(robotsSitemapUrl));
                }
            }
        }

        logger.info("Sitemap discovery found " + urls.size() + " URLs");
        return urls;
    }

    private List<String> fetchAndParseSitemap(String sitemapUrl) {
        List<String> urls = new ArrayList<>();
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(sitemapUrl))
                    .header("User-Agent", "FalconIQCrawler/1.0")
                    .timeout(TIMEOUT)
                    .GET()
                    .build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() != 200) {
                return urls;
            }

            String body = response.body();
            Matcher locMatcher = LOC_PATTERN.matcher(body);
            while (locMatcher.find()) {
                String url = locMatcher.group(1).trim();
                if (url.startsWith("http")) {
                    // Check if this is a sitemap index (references other sitemaps)
                    if (body.contains("<sitemapindex") && url.contains("sitemap")) {
                        urls.addAll(fetchAndParseSitemap(url));
                    } else {
                        urls.add(url);
                    }
                }
            }
            logger.fine("Parsed " + urls.size() + " URLs from " + sitemapUrl);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        } catch (Exception e) {
            logger.fine("Could not fetch sitemap: " + sitemapUrl);
        }
        return urls;
    }
}
