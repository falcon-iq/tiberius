package com.falconiq.crawler.core;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;

import java.net.URI;
import java.util.ArrayList;
import java.util.List;

/**
 * Extracts and normalizes same-domain links from HTML content.
 */
public class LinkExtractor {

    private final String targetHost;

    public LinkExtractor(String targetHost) {
        this.targetHost = targetHost;
    }

    /**
     * Parse HTML and return a list of absolute, normalized, same-domain URLs.
     */
    public List<String> extract(String baseUrl, String html) {
        List<String> links = new ArrayList<>();
        Document doc = Jsoup.parse(html, baseUrl);

        for (Element anchor : doc.select("a[href]")) {
            String href = anchor.absUrl("href");
            if (href.isEmpty()) {
                continue;
            }
            String normalized = normalize(href);
            if (normalized != null && isSameDomain(normalized)) {
                links.add(normalized);
            }
        }
        return links;
    }

    private String normalize(String url) {
        try {
            URI uri = URI.create(url);
            String scheme = uri.getScheme();
            if (scheme == null || (!scheme.equals("http") && !scheme.equals("https"))) {
                return null;
            }
            String path = uri.getPath();
            if (path == null || path.isEmpty()) {
                path = "/";
            } else if (path.length() > 1 && path.endsWith("/")) {
                path = path.substring(0, path.length() - 1);
            }
            URI normalized = new URI(scheme, null, uri.getHost(), uri.getPort(),
                    path, uri.getQuery(), null);
            return normalized.toString();
        } catch (Exception e) {
            return null;
        }
    }

    private boolean isSameDomain(String url) {
        try {
            URI uri = URI.create(url);
            return targetHost.equalsIgnoreCase(uri.getHost());
        } catch (Exception e) {
            return false;
        }
    }
}
