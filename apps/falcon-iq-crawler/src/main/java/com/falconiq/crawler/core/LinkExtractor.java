package com.falconiq.crawler.core;

import com.falconiq.crawler.util.UrlUtils;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;

import java.net.URI;
import java.util.ArrayList;
import java.util.List;

/**
 * Extracts and normalizes same-domain links from HTML content.
 * Uses URL canonicalization to strip tracking params and normalize host/path.
 */
public class LinkExtractor {

    private final String targetHost;
    private final String targetHostNormalized;

    public LinkExtractor(String targetHost) {
        this.targetHost = targetHost;
        // Normalize for www/non-www matching
        this.targetHostNormalized = targetHost.toLowerCase().startsWith("www.")
                ? targetHost.substring(4).toLowerCase()
                : targetHost.toLowerCase();
    }

    /**
     * Parse HTML and return a list of absolute, canonicalized, same-domain URLs.
     */
    public List<String> extract(String baseUrl, String html) {
        List<String> links = new ArrayList<>();
        Document doc = Jsoup.parse(html, baseUrl);

        for (Element anchor : doc.select("a[href]")) {
            String href = anchor.absUrl("href");
            if (href.isEmpty()) {
                continue;
            }
            String canonical = UrlUtils.canonicalize(href);
            if (canonical != null && isSameDomain(canonical)) {
                links.add(canonical);
            }
        }
        return links;
    }

    private boolean isSameDomain(String url) {
        try {
            URI uri = URI.create(url);
            String host = uri.getHost();
            if (host == null) return false;
            host = host.toLowerCase();
            if (host.startsWith("www.")) {
                host = host.substring(4);
            }
            return targetHostNormalized.equals(host);
        } catch (Exception e) {
            return false;
        }
    }
}
