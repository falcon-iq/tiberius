package com.falconiq.crawler.util;

public final class UrlUtils {

    private UrlUtils() {
    }

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
}
