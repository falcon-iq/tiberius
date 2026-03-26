package com.falconiq.crawler.util;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.Set;

public final class UrlUtils {

    private UrlUtils() {
    }

    /** UTM and tracking parameters to strip during canonicalization. */
    private static final Set<String> TRACKING_PARAMS = Set.of(
            "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
            "ref", "fbclid", "gclid", "msclkid", "mc_cid", "mc_eid"
    );

    /**
     * Normalizes a URL by stripping protocol, www prefix, and trailing slash
     * for consistent domain matching.
     */
    public static String normalizeUrl(String url) {
        if (url == null) return "";
        String normalized = url.strip().toLowerCase();
        if (normalized.startsWith("https://")) {
            normalized = normalized.substring(8);
        } else if (normalized.startsWith("http://")) {
            normalized = normalized.substring(7);
        }
        if (normalized.startsWith("www.")) {
            normalized = normalized.substring(4);
        }
        if (normalized.endsWith("/")) {
            normalized = normalized.substring(0, normalized.length() - 1);
        }
        return normalized;
    }

    /**
     * Canonicalize a full URL: strip tracking params, collapse www, remove trailing slash,
     * remove fragment. Returns the canonical URL string, or null if invalid.
     */
    public static String canonicalize(String url) {
        if (url == null || url.isBlank()) return null;
        try {
            URI uri = URI.create(url);
            String scheme = uri.getScheme();
            if (scheme == null || (!scheme.equals("http") && !scheme.equals("https"))) {
                return null;
            }

            // Normalize host: strip www.
            String host = uri.getHost();
            if (host == null) return null;
            host = host.toLowerCase();
            if (host.startsWith("www.")) {
                host = host.substring(4);
            }

            // Normalize path: strip trailing slash
            String path = uri.getPath();
            if (path == null || path.isEmpty()) {
                path = "/";
            } else if (path.length() > 1 && path.endsWith("/")) {
                path = path.substring(0, path.length() - 1);
            }

            // Strip tracking query params
            String query = stripTrackingParams(uri.getQuery());

            return new URI(scheme, null, host, uri.getPort(), path, query, null).toString();
        } catch (URISyntaxException | IllegalArgumentException e) {
            return null;
        }
    }

    private static String stripTrackingParams(String query) {
        if (query == null || query.isBlank()) return null;

        StringBuilder cleaned = new StringBuilder();
        for (String param : query.split("&")) {
            String key = param.contains("=") ? param.substring(0, param.indexOf('=')) : param;
            if (!TRACKING_PARAMS.contains(key.toLowerCase())) {
                if (!cleaned.isEmpty()) {
                    cleaned.append('&');
                }
                cleaned.append(param);
            }
        }
        return cleaned.isEmpty() ? null : cleaned.toString();
    }
}
